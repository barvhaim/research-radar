.PHONY: format lint help install run mcp-server mcp-test

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


# Display help information
help:
	@echo "Available commands:"
	@echo "  make format      - Format code with black"
	@echo "  make lint        - Lint code with pylint"
	@echo "  make install     - Install dependencies with uv"
	@echo "  make run         - Run the main workflow"
	@echo "  make mcp-server  - Run the MCP Server (SSE on port 5555)"
	@echo "  make help        - Display this help message"
