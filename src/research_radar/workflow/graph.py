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
    Router: Checks if input ID is a Paper (Arxiv) or YouTube Video.
    Used for determining the entry point state.
    """
    input_id = state.get("paper_id", "")
    
    if "." in input_id and input_id.replace(".", "").isdigit():
        return "extract_paper_information"
    
    return "extract_youtube_information"

def build_graph():
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
