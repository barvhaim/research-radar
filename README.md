# Research Radar

<img src="logo.png" alt="Research Radar Logo" width="400"/>

A research paper discovery and analysis tool that uses AI to extract, analyze, and process academic papers.

## Quick Start

### Prerequisites
- Python 3.11.13+
- Node.js 18+ and npm
- [uv](https://docs.astral.sh/uv/) package manager
- Ollama (for local LLM inference)

### Installation

```bash
# Install Python dependencies
make install

# Install frontend dependencies
cd frontend
npm install
cd ..

# Configure environment
cp .env.example .env
# Edit .env to set LLM_PROVIDER and LLM_MODEL
```

### Usage

#### Option 1: FastAPI + React UI (Recommended)

**Development Mode** (with hot reload):

```bash
# Terminal 1 - Backend
source .venv/bin/activate
python -m research_radar.api.server

# Terminal 2 - Frontend
cd frontend
npm run dev
```

Access at `http://localhost:5173`

**Production Mode**:

```bash
# Build frontend
cd frontend
npm run build
cd ..

# Run server (serves both API and UI)
source .venv/bin/activate
python -m research_radar.api.server
```

Access at `http://localhost:8000`

See [SETUP.md](SETUP.md) for detailed setup instructions.

#### Option 2: Gradio UI (Legacy)

```bash
make ui
```

Then open your browser to `http://127.0.0.1:7860` and enter a paper ID (e.g., `2510.24081`)

#### Option 3: Command Line

```bash
# Run the example workflow
make run
```

#### Option 4: MCP Server (for Claude Desktop integration)

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
