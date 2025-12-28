"""Module defining the workflow graph for paper processing."""

from langgraph.graph import StateGraph
from research_radar.workflow.state import WorkflowState
from research_radar.workflow.node_types import (
    EXTRACT_PAPER_INFORMATION,
    FILTER_PAPER_RELEVANCE,
    EXTRACT_PAPER_CONTENT,
    EMBED_PAPER,
    ANALYZE_PAPER,
    PUBLISH_RESULTS,
)

from research_radar.workflow.nodes import (
    extract_paper_information_node,
    filter_paper_relevance_node,
    extract_paper_content_node,
    embed_paper_node,
    analyze_paper_node,
    publish_results_node,
)


def build_graph():
    """Build and compile the paper processing workflow graph."""
    flow = StateGraph(WorkflowState)

    flow.add_node(EXTRACT_PAPER_INFORMATION, extract_paper_information_node)
    flow.add_node(FILTER_PAPER_RELEVANCE, filter_paper_relevance_node)
    flow.add_node(EXTRACT_PAPER_CONTENT, extract_paper_content_node)
    flow.add_node(EMBED_PAPER, embed_paper_node)
    flow.add_node(ANALYZE_PAPER, analyze_paper_node)
    flow.add_node(PUBLISH_RESULTS, publish_results_node)

    flow.set_entry_point(EXTRACT_PAPER_INFORMATION)

    return flow.compile()
