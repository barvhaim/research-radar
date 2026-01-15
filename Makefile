# Format Python code with black
format:
	uv run black .

# Lint Python code with pylint
lint:
	uv run pylint src/research_radar

# Install dependencies
install:
	uv sync

# Run the main workflow
run:
	uv run python workflow.py

# Run the MCP Server with SSE transport
mcp-server:
	uv run python -m mcp_server.server

# Run the Gradio UI web interface
ui:
	uv run python -m research_radar.ui.app

# Run the FastAPI server (development mode)
api:
	uv run python -m research_radar.api.server

# Build the React frontend
build-frontend:
	cd frontend && npm install && npm run build

# Run full stack (build frontend + run API server)
serve:
	cd frontend && npm run build && cd .. && uv run python -m research_radar.api.server

# Install all dependencies (Python + Node.js)
install-all: install
	cd frontend && npm install

# Display help information
help:
	@echo "Available commands:"
	@echo "  make format          - Format code with black"
	@echo "  make lint            - Lint code with pylint"
	@echo "  make install         - Install Python dependencies with uv"
	@echo "  make install-all     - Install Python + Node.js dependencies"
	@echo "  make run             - Run the main workflow"
	@echo "  make ui              - Run the Gradio UI web interface (port 7860)"
	@echo "  make api             - Run the FastAPI server (port 8000)"
	@echo "  make build-frontend  - Build the React frontend"
	@echo "  make serve           - Build frontend and run API server (production)"
	@echo "  make mcp-server      - Run the MCP Server (SSE on port 5555)"
	@echo "  make help            - Display this help message"
