# Research Radar

A research paper discovery and analysis tool that uses LangGraph workflows to extract, analyze, and process academic papers.

## Quick Start

### Prerequisites
- Python 3.11.13+
- [uv](https://docs.astral.sh/uv/) package manager
- Ollama (for local LLM inference)

### Installation

```bash
# Install dependencies
make install

# Configure environment
cp .env.example .env
# Edit .env to set LLM_PROVIDER and LLM_MODEL
```

### Usage

```bash
# Run the example workflow
make run
```

## Development

```bash
# Format code
make format

# Lint code
make lint
```


## License

MIT License - see [LICENSE](LICENSE) file for details
