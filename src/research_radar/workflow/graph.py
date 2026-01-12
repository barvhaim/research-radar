"""Module defining the workflow graph for paper processing."""

import re

from langgraph.graph import StateGraph
from research_radar.workflow.state import WorkflowState
from research_radar.workflow.node_types import (
    EXTRACT_PAPER_INFORMATION,
    EXTRACT_YOUTUBE_INFORMATION,
    FILTER_PAPER_RELEVANCE,
    EXTRACT_PAPER_CONTENT,
    EXTRACT_YOUTUBE_CONTENT,
    EMBED_CONTENT,
    ANALYZE_PAPER,
    PUBLISH_RESULTS,
)

from research_radar.workflow.nodes import (
    extract_paper_information_node,
    extract_youtube_information_node,
    filter_paper_relevance_node,
    extract_paper_content_node,
    extract_youtube_content_node,
    embed_content_node,
    analyze_paper_node,
    publish_results_node,
)

def route_source_type(state: dict) -> str:
    """
    Router: Uses regex to check if input is an ArXiv ID/URL or a YouTube URL.
    """
    input_id = state.get("paper_id", "").strip()
    
    youtube_pattern = r"(youtube\.com|youtu\.be|^[a-zA-Z0-9_-]{11}$)"
    
    if re.search(youtube_pattern, input_id):
        return "extract_youtube_information"
    
    return "extract_paper_information"

def build_graph():
    """Build and compile the paper processing workflow graph."""
    flow = StateGraph(WorkflowState)

    flow.add_node(EXTRACT_PAPER_INFORMATION, extract_paper_information_node)
    flow.add_node(EXTRACT_YOUTUBE_INFORMATION, extract_youtube_information_node)
    flow.add_node(FILTER_PAPER_RELEVANCE, filter_paper_relevance_node)
    flow.add_node(EXTRACT_PAPER_CONTENT, extract_paper_content_node)
    flow.add_node(EXTRACT_YOUTUBE_CONTENT, extract_youtube_content_node)
    flow.add_node(EMBED_CONTENT, embed_content_node)
    flow.add_node(ANALYZE_PAPER, analyze_paper_node)
    flow.add_node(PUBLISH_RESULTS, publish_results_node)

    flow.set_conditional_entry_point(
        route_source_type,
        {
            "extract_paper_information": EXTRACT_PAPER_INFORMATION,
            "extract_youtube_information": EXTRACT_YOUTUBE_INFORMATION
        }
    )


    return flow.compile()
