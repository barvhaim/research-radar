#!/usr/bin/env -S uv run
"""
Example script demonstrating how to use the LangGraph workflow for research paper analysis.

Usage:
    uv run workflow.py
"""

import uuid
import logging
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from research_radar.workflow.graph import build_graph
from research_radar.workflow.state import WorkflowStatus


logger = logging.getLogger(__name__)
console = Console()


def configure_logging():
    """Configure logging for the workflow."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def print_header():
    """Print workflow header."""
    console.print(
        Panel.fit(
            "[bold cyan]Research Paper Analysis[/bold cyan]",
            border_style="cyan",
        )
    )


def create_initial_state(paper_id: str) -> dict:
    """Create initial workflow state.

    Args:
        paper_id: ID of paper.

    Returns:
        Initial workflow state dictionary.
    """
    return {
        "workflow_id": str(uuid.uuid4()),
        "paper_id": paper_id,
        "metadata": None,
        "content": None,
        "status": WorkflowStatus.PENDING.value,
        "error": None,
        "required_keywords": ["large language models (LLMs)",
        "instruction following (IF)",
        "multi-turn instructions",
        "system-prompted instructions",
        "human-annotated benchmarks",
        "rubrics",
        "LLMs",
        "commonsense reasoning",
        "Global PIQA",
        "language varieties",
        "culturally-specific elements",],
    }


def print_initial_state(state: dict):
    """Print the initial workflow state.

    Args:
        state: Initial workflow state dictionary.
    """
    console.print("\n[bold]Initial State:[/bold]")
    console.print(f"  Workflow ID: [yellow]{state['workflow_id']}[/yellow]")
    console.print(f"  Paper ID: [blue]{state['paper_id']}[/blue]")


def build_results_table(result: dict) -> Table:
    """Build a rich table with workflow results.

    Args:
        result: Workflow result dictionary.

    Returns:
        Formatted rich Table object.
    """
    table = Table(
        title="Workflow Execution Results",
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("Field", style="cyan", width=15)
    table.add_column("Value", style="green")

    table.add_row("Status", result.get("status", "unknown"))

    if result.get("error"):
        table.add_row("Error", f"[red]{result['error']}[/red]")

    return table


def print_results(result: dict):
    """Print workflow results.

    Args:
        result: Workflow result dictionary.
    """
    table = build_results_table(result)
    console.print("\n", table)
    console.print(
        f"\n[bold green]✓[/bold green] Workflow finished for paper [blue]{result['paper_id']}[/blue]\n"
    )


def run_workflow(paper_id: str):
    """Run the paper analysis workflow.

    Args:
        paper_id: ID of paper.
    """
    configure_logging()
    print_header()

    # Build the workflow graph
    graph = build_graph()

    # Create and display initial state
    initial_state = create_initial_state(paper_id=paper_id)
    print_initial_state(initial_state)

    # Execute the workflow
    with console.status("[bold green]Executing workflow...", spinner="dots"):
        result = graph.invoke(initial_state)

    # Display results
    print_results(result)


def main():
    """Main entry point."""
    paper_id = "2510.24081"  # https://huggingface.co/api/papers/2510.24081
    run_workflow(paper_id=paper_id)


if __name__ == "__main__":
    main()
