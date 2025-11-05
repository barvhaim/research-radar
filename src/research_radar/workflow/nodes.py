import logging
from langgraph.graph import END
from langgraph.types import Command
from research_radar.workflow.state import WorkflowState, WorkflowStatus
from research_radar.core.paper_metadata_extractor import PaperMetadataExtractor
from research_radar.workflow.node_types import (
    EXTRACT_PAPER_CONTENT,
    ANALYZE_PAPER,
    PUBLISH_RESULTS,
)


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

    # TODO: Implement actual metadata extraction logic
    extractor = PaperMetadataExtractor(paper_id=paper_id)
    metadata = extractor.extract_metadata()

    return Command(
        goto=EXTRACT_PAPER_CONTENT,
        update={
            "status": WorkflowStatus.RUNNING.value,
            "metadata": metadata,
        },
    )


def extract_paper_content_node(state: WorkflowState) -> Command:
    """
    Node that performs paper content extraction.

    Args:
        state (PipelineState): The current state of the workflow.

    Returns:
        Command: A command to execute the content extraction.
    """

    logger.info("Extracting paper content")

    # TODO: Get paper PDF url from state starting now
    # TODO: Implement content extraction logic

    return Command(
        goto=ANALYZE_PAPER,
        update={},
    )


def analyze_paper_node(state: WorkflowState) -> Command:
    """
    Node that performs paper analysis.
    :param state:
    :return:
    """

    logger.info("Analyzing paper content")

    # TODO: Implement paper analysis logic
    return Command(
        goto=PUBLISH_RESULTS,
        update={},
    )


def publish_results_node(state: WorkflowState) -> Command:
    """
    Node that publishes the results of the analysis.
    :param state:
    :return:
    """

    logger.info("Publishing analysis results")

    # TODO: Implement results publishing logic
    return Command(
        goto=END,
        update={
            "status": WorkflowStatus.COMPLETED.value,
        },
    )
