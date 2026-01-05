import logging
from langgraph.graph import END
from langgraph.types import Command

from research_radar.workflow.state import WorkflowState, WorkflowStatus
from research_radar.core.paper_metadata_extractor import PaperMetadataExtractor
from research_radar.core.paper_relevance_checker import PaperRelevanceChecker
from research_radar.core.paper_content_extractor import PaperContentExtractor
from research_radar.core.youtube_metadata_extractor import YouTubeMetadataExtractor
from research_radar.core.youtube_content_extractor import YouTubeContentExtractor
from research_radar.core.paper_rag_processor import PaperRAGProcessor
from research_radar.core.paper_analyzer import PaperAnalyzer
from research_radar.workflow.node_types import (
    EXTRACT_PAPER_CONTENT,
    ANALYZE_PAPER,
    PUBLISH_RESULTS,
    FILTER_PAPER_RELEVANCE,
    EMBED_CONTENT,
    EXTRACT_PAPER_INFORMATION,
)

rag_processor = PaperRAGProcessor()  # Global instance to manage RAG pipline

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
            "type": "paper",
        },
    )

def extract_youtube_information_node(state: WorkflowState) -> Command:
    """
    Node that performs YouTube metadata extraction.
    """
    video_id = state.get("paper_id")
    if not video_id:
        return Command(goto=END, update={"error": "No Video ID provided."})

    logger.info("Extracting YouTube video (%s) information", video_id)

    extractor = YouTubeMetadataExtractor(video_id=video_id)
    metadata = extractor.extract_metadata()

    if metadata is None:
        return Command(
            goto=END,
            update={
                "status": WorkflowStatus.FAILED.value,
                "error": f"Metadata extraction failed for video {video_id}.",
            },
        )
    
    return Command(
        goto=FILTER_PAPER_RELEVANCE, 
        update={
            "status": WorkflowStatus.RUNNING.value,
            "metadata": metadata,
            "source_type": "youtube" 
        },
    )

def filter_paper_relevance_node(state: WorkflowState) -> Command:
    """
    Node that filters the paper (or video) based on keyword relevance,
    using the PaperRelevanceChecker class.

    Args:
        state (WorkflowState): The current state of the workflow.

    Returns:
        Command: A command to continue or end the workflow.
    """
    metadata = state.get("metadata")
    required_keywords = state.get("required_keywords", [])
    paper_id = state.get("paper_id")

    source_type = state.get("source_type", "paper")
    
    if source_type == "youtube":
        target_content_node = "extract_youtube_content" 
    else:
        target_content_node = EXTRACT_PAPER_CONTENT

    if not metadata:
        logger.warning(
            f"Filter Error: Missing metadata or required_keywords for paper %s. Ending workflow.",
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
        logger.info(f"No required keywords specified. Skipping relevance check.")
        return Command(
            goto=target_content_node, 
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
        next_node = target_content_node 
        logger.info(
            f"Item %s: Determined relevant. Routing to: %s",
            paper_id, next_node
        )
        status = WorkflowStatus.RUNNING.value
    else:
        next_node = END
        logger.warning(
            f"Item %s: Not relevant after all checks. Ending workflow.", paper_id
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
        goto=EMBED_CONTENT,
        update={
            "content": content,
        },
    )

def extract_youtube_content_node(state: WorkflowState) -> Command:
    """
    Node that performs YouTube transcript extraction.
    """
    video_id = state.get("paper_id")
    logger.info("Extracting YouTube content for: %s", video_id)

    try:
        extractor = YouTubeContentExtractor(source=video_id)
        transcript = extractor.extract_content()

        if not transcript:
            return Command(
                goto=END, 
                update={"error": "Failed to extract transcript (no subtitles found)."}
            )
            
        return Command(
            goto=EMBED_CONTENT,
            update={
                "content": transcript
            }
        )

    except Exception as e:
        logger.error(f"Content extraction failed: {e}")
        return Command(goto=END, update={"error": str(e)})

def embed_content_node(state: WorkflowState) -> Command:
    """
    Node that embeds the extracted text into the vector database.

    Args:
        state (WorkflowState): The current state of the workflow.

    Returns:
        Command: A command to continue or end the workflow.
    """

    logger.info("Embedding paper content into RAG system")

    # Get data
    content = state.get("content")
    metadata = state.get("metadata", {})
    paper_id = state.get("paper_id")

    # Prepare data for RAG processor
    paper_data = {
        "paper_url": metadata.get("arxiv_pdf_url", paper_id),
        "text_content": content,
        "metadata": metadata,
    }

    # Run RAG processor
    try:
        paper_hash_id = rag_processor.process_paper(paper_data)

        if not paper_hash_id:
            return Command(goto=END, update={"error": "Embedding failed."})

        logger.info("Paper embedded successfully. Hash: %s", paper_hash_id[:8])

        return Command(
            goto=ANALYZE_PAPER,
            update={"paper_hash_id": paper_hash_id},
        )

    except Exception as e:
        logger.error("Embedding failed: %s", e)
        return Command(goto=END, update={"error": str(e)})


def analyze_paper_node(state: WorkflowState) -> Command:
    """
    Node that performs paper analysis.
    :param state: analysis
    :return:
        command: A command to generate an initial summary of paper.
    """

    logger.info("Analyzing paper content")

    paper_hash_id = state.get("paper_hash_id")

    if not paper_hash_id:
        logger.warning("Received NO paper hash ID. Skipping analysis.")
        return Command(
            goto=PUBLISH_RESULTS, update={"error": "Analysis skipped (No RAG data)."}
        )

    analyzer = PaperAnalyzer(rag_processor)

    try:
        analysis = analyzer.generate_analysis(paper_hash_id)
        summary = analyzer.generate_summary(analysis)

        return Command(
            goto=PUBLISH_RESULTS,
            update={
                "analysis": analysis,
                "summary": summary,
            },
        )

    except Exception as e:
        logger.error("Analysis failed: %s", e)
        return Command(goto=END, update={"error": str(e)})


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
