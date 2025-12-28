"""Module containing workflow node implementations for paper processing."""

import logging
from langgraph.graph import END
from langgraph.types import Command


from research_radar.workflow.state import WorkflowState, WorkflowStatus
from research_radar.core.paper_metadata_extractor import PaperMetadataExtractor
from research_radar.core.paper_relevance_checker import PaperRelevanceChecker
from research_radar.core.paper_content_extractor import PaperContentExtractor
from research_radar.workflow.node_types import (
    EXTRACT_PAPER_CONTENT,
    ANALYZE_PAPER,
    PUBLISH_RESULTS,
    FILTER_PAPER_RELEVANCE,
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
        return Command(goto=END, update={"error": "No paper ID provided."})

    logger.info(
        "Extracting paper (%s) information",
        paper_id,
    )

    extractor = PaperMetadataExtractor(paper_id=paper_id)
    metadata = extractor.extract_metadata()

    if metadata is None:
        error_message = f"Metadata extraction failed for paper {paper_id}."
        return Command(
            goto=END,
            update={
                "status": WorkflowStatus.FAILED.value,
                "error": error_message,
            },
        )
    return Command(
        goto=FILTER_PAPER_RELEVANCE,
        update={
            "status": WorkflowStatus.RUNNING.value,
            "metadata": metadata,
        },
    )


def filter_paper_relevance_node(state: WorkflowState) -> Command:
    """
    Node that filters the paper based on keyword relevance,
    using the PaperRelevanceChecker class.

    Args:
        state (WorkflowState): The current state of the workflow.

    Returns:
        Command: A command to continue or end the workflow.
    """
    metadata = state.get("metadata")
    required_keywords = state.get("required_keywords", [])
    paper_id = state.get("paper_id")

    # Validation check
    if not metadata:
        logger.warning(
            "Filter Error: Missing metadata or required_keywords for paper %s. Ending workflow.",
            paper_id,
        )
        return Command(
            goto=END,
            update={
                "status": WorkflowStatus.FAILED.value,
                "error": "Missing metadata or required keywords for relevance check.",
            },
        )
    if not required_keywords:
        logger.info("No required keywords specified. Skipping relevance check.")
        return Command(
            goto=EXTRACT_PAPER_CONTENT,
            update={
                "status": WorkflowStatus.RUNNING.value,
            },
        )

    checker = PaperRelevanceChecker(
        metadata=metadata,
        required_keywords=required_keywords,
    )

    is_relevant = checker.check_relevance(state)

    if is_relevant:
        next_node = EXTRACT_PAPER_CONTENT
        logger.info(
            "Paper %s: Determined relevant. Continuing to content extraction.",
            paper_id,
        )
        status = WorkflowStatus.RUNNING.value
    else:
        next_node = END
        logger.warning(
            "Paper %s: Not relevant after all checks. Ending workflow.", paper_id
        )
        status = WorkflowStatus.COMPLETED.value

    return Command(
        goto=next_node,
        update={
            "status": status,
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

    source = state.get("metadata", {}).get("arxiv_pdf_url")
    if not source:
        raise ValueError("Error: arxiv url is missing or None.")

    extractor = PaperContentExtractor(source)
    content = extractor.extract_content()

    return Command(
        goto=ANALYZE_PAPER,
        update={
            "content": content,
        },
    )


def analyze_paper_node(
    state: WorkflowState,
) -> Command:  # pylint: disable=unused-argument
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


def publish_results_node(
    state: WorkflowState,
) -> Command:  # pylint: disable=unused-argument
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
