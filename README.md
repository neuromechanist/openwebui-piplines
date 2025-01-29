# OpenWebUI Pipelines

A collection of AI model pipelines for OpenWebUI, including a combined Perplexity-Anthropic pipeline that leverages Perplexity's search capabilities with Anthropic's analysis.

## Features

- **Combined Sonar-Sonnet Pipeline**: Integrates Perplexity's Sonar Small model for web search with Claude 3.5 Sonnet for comprehensive analysis
- **Conversation-Aware**: Maintains context across multiple interactions for more coherent responses
- **Citation Support**: Automatically includes references to source materials
- **Flexible Architecture**: Easy to extend with additional pipelines

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/openwebui-piplines.git
cd openwebui-piplines
```

2. Set up your environment variables:
```bash
export PERPLEXITY_API_KEY="your_perplexity_api_key"
export ANTHROPIC_API_KEY="your_anthropic_api_key"
```

Alternatively, use the OpenWebUI configuration file or the User Interface to set these values.

## Usage

The pipelines can be integrated with OpenWebUI. Each pipeline provides specific capabilities:

### Combined Sonar-Sonnet Pipeline

This pipeline combines Perplexity's search capabilities with Anthropic's analysis:

1. Performs web searches using Perplexity's Sonar Small model
2. Analyzes search results using Claude 3.5 Sonnet
3. Maintains conversation context for coherent multi-turn interactions
4. Provides cited sources for information

## Requirements

- Python 3.7+
- requests
- sseclient-py
- pydantic

## License

This project is licensed under the BSD 3-Clause License - see the [LICENSE](LICENSE) file for details.
