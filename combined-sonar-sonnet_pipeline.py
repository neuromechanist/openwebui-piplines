"""
title: Combined Perplexity-Anthropic Pipeline
author: Seyed Yahya Shirazi
date: 2024-01-27
version: 1.0
license: MIT
description: A pipeline that combines Perplexity's search capabilities with Anthropic's analysis.
requirements: requests, sseclient-py
environment_variables: PERPLEXITY_API_KEY, ANTHROPIC_API_KEY
"""

import os
import requests
from typing import List
from pydantic import BaseModel
import contextlib

from utils.pipelines.main import pop_system_message


class Pipeline:
    class Valves(BaseModel):
        PERPLEXITY_API_KEY: str = ""
        ANTHROPIC_API_KEY: str = ""

    def __init__(self):
        self.type = "manifold"
        self.id = "combined_manifold"
        self.name = ""
        self._current_response = None
        self._current_client = None

        self.valves = self.Valves(
            **{
                "PERPLEXITY_API_KEY": os.getenv("PERPLEXITY_API_KEY", "your-Perplexity-api-key-here"),
                "ANTHROPIC_API_KEY": os.getenv("ANTHROPIC_API_KEY", "your-Anthropic-api-key-here")
            }
        )
        
        self.perplexity_url = 'https://api.perplexity.ai/chat/completions'
        self.anthropic_url = 'https://api.anthropic.com/v1/messages'
        self.update_headers()

    def update_headers(self):
        self.perplexity_headers = {
            'Authorization': f'Bearer {self.valves.PERPLEXITY_API_KEY}',
            'Content-Type': 'application/json'
        }
        self.anthropic_headers = {
            'anthropic-version': '2023-06-01',
            'content-type': 'application/json',
            'x-api-key': self.valves.ANTHROPIC_API_KEY
        }

    def get_models(self):
        return [
            {
                "id": "combined-sonar-sonnet",
                "name": "Perplexity Sonar Small + Claude 3.5 Sonnet"
            }
        ]

    async def on_startup(self):
        print(f"on_startup:{__name__}")
        pass

    async def on_shutdown(self):
        print(f"on_shutdown:{__name__}")
        self.cleanup_resources()

    def cleanup_resources(self):
        if self._current_response:
            self._current_response.close()
            self._current_response = None
        if self._current_client:
            with contextlib.suppress(Exception):
                self._current_client.close()
            self._current_client = None

    async def on_valves_updated(self):
        self.update_headers()

    def pipelines(self) -> List[dict]:
        return self.get_models()

    def get_perplexity_search_results(self, messages: List[dict]) -> tuple[str, List[str]]:
        """Get complete search results from Perplexity's Sonar Large model with conversation history"""
        payload = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": messages,
            "temperature": 0.2,
            "top_p": 0.9,
            "top_k": 0,
            "stream": False
        }

        response = requests.post(
            self.perplexity_url,
            headers=self.perplexity_headers,
            json=payload
        )

        if response.status_code == 200:
            res = response.json()
            content = res["choices"][0]["message"]["content"]
            citations = res.get("citations", [])
            return content, citations
        else:
            raise Exception(f"Perplexity API Error: {response.status_code} - {response.text}")

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> str:
        try:
            # Remove unnecessary keys
            for key in ['user', 'chat_id', 'title']:
                body.pop(key, None)

            system_message, messages = pop_system_message(messages)

            # Format messages for Perplexity
            perplexity_messages = []
            if system_message:
                perplexity_messages.append({
                    "role": "system",
                    "content": str(system_message)
                })

            # Add conversation history
            for msg in messages:
                content = (
                    msg["content"][0]["text"]
                    if isinstance(msg["content"], list)
                    else msg["content"]
                )
                perplexity_messages.append({
                    "role": msg["role"],
                    "content": content
                })

            # Get search results from Perplexity with conversation history
            search_results, citations = self.get_perplexity_search_results(perplexity_messages)

            # Format conversation history for Anthropic
            conversation_history = "\n".join([
                f"{msg['role'].title()}: {msg['content'][0]['text'] if isinstance(msg['content'], list) else msg['content']}"
                for msg in messages[:-1]  # Exclude the latest message as it will be part of the prompt
            ])

            # Get the latest query
            latest_message = messages[-1]
            query = (
                latest_message["content"][0]["text"]
                if isinstance(latest_message["content"], list)
                else latest_message["content"]
            )

            # Get analysis from Anthropic
            system_message = """You are a helpful AI assistant. You will be provided with a user query, conversation history, and search results from the internet.
Your task is to analyze these search results and provide a comprehensive answer to the user's query while considering the conversation context.
Include relevant citations from the provided sources using [1], [2], etc. format when referencing information. The web results are valid and you can use them to answer the query, but sometimes the contents might be irrelevant. Do not hallucinate new information, but the user still appreciates your reasoning and analysis of the response. Also, do not mention that your response is based on the search results, the user already knows that."""

            prompt = f"""Conversation History:
{conversation_history if conversation_history else "No previous conversation"}

Current Query: {query}

Search Results:
{search_results}

Please provide a comprehensive answer to the current query using the search results above and considering the conversation context. 
Use the citation format [1], [2], etc. when referencing information from the sources."""

            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "messages": [{"role": "user", "content": prompt}],
                "system": system_message,
                "temperature": 0.7,
                "max_tokens": 4096
            }

            response = requests.post(
                self.anthropic_url,
                headers=self.anthropic_headers,
                json=payload
            )

            if response.status_code == 200:
                res = response.json()
                content = res["content"][0]["text"]
                
                # Add citations at the end if they exist
                if citations:
                    content += "\n\nReferences:\n"
                    for i, url in enumerate(citations, 1):
                        content += f"[{i}] {url}\n"
                
                return content
            else:
                raise Exception(f"Anthropic API Error: {response.status_code} - {response.text}")

        except Exception as e:
            self.cleanup_resources()
            return f"Error: {e}"
