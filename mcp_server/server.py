from fastmcp import FastMCP
from mcp_server.workflow_adapter import run_workflow_for_paper

mcp = FastMCP("research-radar-mcp")


@mcp.tool()
async def summarize_paper(paper_id: str) -> dict:
    """
    Run the research-radar workflow for the given paper ID
    and return the final summary.

    Args:
        paper_id: The Hugging Face paper ID

    Returns:
        A dictionary with paper_id and summary
    """
    return run_workflow_for_paper(paper_id)


def main():
    mcp.run(transport="sse", host="127.0.0.1", port=5555)


if __name__ == "__main__":
    main()
