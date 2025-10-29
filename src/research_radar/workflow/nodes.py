import logging
from langgraph.graph import END
from langgraph.types import Command
from research_radar.workflow.state import WorkflowState, WorkflowStatus


logger = logging.getLogger(__name__)


def extract_paper_information_node(state: WorkflowState) -> Command:
    """
    Node that performs paper metadata extraction.

    Args:
        state (PipelineState): The current state of the workflow.

    Returns:
        Command: A command to execute the metadata extraction.
    """
    paper_id = state.get("paper_id")
    if not paper_id:
        return Command(goto=END, update={"error": "No paper id provided."})

    logger.info(
        "Extracting paper (%s) information",
        paper_id,
    )

    metadata = {}  # TODO

    return Command(
        goto=END,
        update={
            "status": WorkflowStatus.RUNNING.value,
            "metadata": metadata,
        },
    )
