# Research Radar

<img src="logo.png" alt="Research Radar Logo" width="400"/>

A research paper discovery and analysis tool that uses AI to extract, analyze, and process academic papers.

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

#### Option 1: Web UI (Recommended)

```bash
make ui
```

Then open your browser to `http://127.0.0.1:7860` and enter a paper ID (e.g., `2510.24081`)

#### Option 2: Command Line

```bash
# Run the example workflow
make run
```

#### Option 3: MCP Server (for Claude Desktop integration)

```bash
make mcp-server
```

This starts the MCP server on port 5555, allowing Claude Desktop to use the `summarize_paper` tool.

## Development

```bash
# Format code
make format

# Lint code
make lint
```


## License

MIT License - see [LICENSE](LICENSE) file for details
