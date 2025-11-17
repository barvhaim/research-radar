import logging
from langgraph.graph import END
from langgraph.types import Command

from research_radar.llm.client import get_chat_llm_client
from langchain_core.messages import HumanMessage

from research_radar.workflow.state import WorkflowState, WorkflowStatus
from research_radar.core.paper_metadata_extractor import PaperMetadataExtractor
from research_radar.core.paper_relevance_checker import PaperRelevanceChecker
from research_radar.workflow.node_types import (
    EXTRACT_PAPER_CONTENT,
    ANALYZE_PAPER,
    PUBLISH_RESULTS,
    FILTER_PAPER_RELEVANCE,
    EXTRACT_PAPER_INFORMATION,
    LLM_RELEVANCE_CHECK,
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

    # TODO: Implement actual metadata extraction logic
    extractor = PaperMetadataExtractor(paper_id=paper_id)
    metadata = extractor.extract_metadata()

    if metadata is None:
        error_message = f"Metadata extraction failed for paper {paper_id}."
        return Command(
            goto=END,
            update={
                "status": WorkflowStatus.FAILED.value,
                "error": error_message,  # <--- הוספת הודעת שגיאה ברורה
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
    if not metadata or not required_keywords:
        logger.warning(
            f"Filter Error: Missing metadata or required_keywords for paper {paper_id}. Ending workflow."
        )
        return Command(
            goto=END,
            update={
                "status": WorkflowStatus.FAILED.value,
                "error": "Missing metadata or required keywords for relevance check.",
            },
        )
    ai_keywords_string: str = metadata.get("ai_keywords", "")
    if not ai_keywords_string:
        logger.info(
            f"Paper {paper_id}: No AI keywords found. Directing to LLM for summary review."
        )
        next_node = LLM_RELEVANCE_CHECK

    else:
        checker = PaperRelevanceChecker(
            metadata=metadata,
            required_keywords=required_keywords,
        )

    is_relevant = checker.check_relevance()

    if is_relevant:
        next_node = EXTRACT_PAPER_CONTENT
    else:
        logger.info(
            f"Paper {paper_id}: Keyword match failed. Directing to LLM for second check."
        )
        next_node = LLM_RELEVANCE_CHECK

    return Command(
        goto=next_node,
        update={
            "status": WorkflowStatus.RUNNING.value,
        },
    )
    # We pass the result to the state. The conditional edge in graph.py decides the next step.


def llm_relevance_check_node(state: WorkflowState) -> Command:
    """
    Node that uses an LLM (Ollama) to check relevance based on the abstract (summary).
    """
    paper_id = state.get("paper_id")

    metadata = state.get("metadata")
    if metadata is None:
        logger.warning(
            f"LLM Check Error: Metadata is None for paper {paper_id}. Cannot proceed."
        )
        return Command(
            goto=END,
            update={
                "error": "Metadata is missing for LLM check.",
            },
        )
    required_keywords = state.get("required_keywords", [])

    abstract_text = metadata.get("summary")

    if not abstract_text:
        logger.warning(
            f"LLM Check Error: Missing abstract (summary) for paper {paper_id}. Cannot proceed. Ending."
        )
        return Command(
            goto=END,
            update={
                "error": "Missing abstract to perform LLM relevance check.",
            },
        )

    logger.info("Executing LLM relevance check using the paper's Abstract.")
    prompt = (
        f"You are a research paper filter specializing in **AI (Artificial Intelligence)**. "
        f"Your goal is to determine if the given abstract is highly relevant to the user's research focus in this technical field. "
        f"**Crucial Rule:** The paper is only relevant if the keywords (e.g., 'Layer Separation', 'Batch Processing') refer to **technical, computational, or scientific concepts**, NOT analogies (e.g., baking, cooking, or general industry practices). "
        f"User Focus Keywords: {', '.join(required_keywords)}. "
        f"Abstract: {abstract_text}. "
        f"Answer STRICTLY with 'YES' or 'NO'."
    )

    try:
        llm_client = get_chat_llm_client()
        response = llm_client.invoke([HumanMessage(content=prompt)])
        llm_decision_raw = response.content.strip().upper()

    except Exception as e:
        logger.error(f"Ollama execution failed for paper {paper_id}. Error: {e}")
        llm_decision_raw = "NO"

    llm_decision = llm_decision_raw == "YES"

    logger.info(f"LLM Decision for paper {paper_id}: {llm_decision}")

    next_node = EXTRACT_PAPER_CONTENT if llm_decision else END
    return Command(
        goto=next_node,
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

    # TODO: Get paper PDF url from state
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
