from langgraph.graph import StateGraph, END
from research_radar.workflow.state import WorkflowState
from research_radar.workflow.node_types import (
    EXTRACT_PAPER_INFORMATION,
    FILTER_PAPER_RELEVANCE,
    EXTRACT_PAPER_CONTENT,
    ANALYZE_PAPER,
    PUBLISH_RESULTS,
    LLM_RELEVANCE_CHECK,

)

from research_radar.workflow.nodes import (
    extract_paper_information_node,
    filter_paper_relevance_node,
    extract_paper_content_node,
    analyze_paper_node,
    publish_results_node,
    llm_relevance_check_node,

)



def build_graph():
    flow = StateGraph(WorkflowState)


    flow.add_node(EXTRACT_PAPER_INFORMATION, extract_paper_information_node)
    flow.add_node(FILTER_PAPER_RELEVANCE, filter_paper_relevance_node)
    flow.add_node(LLM_RELEVANCE_CHECK, llm_relevance_check_node)
    flow.add_node(EXTRACT_PAPER_CONTENT, extract_paper_content_node)
    flow.add_node(ANALYZE_PAPER, analyze_paper_node)
    flow.add_node(PUBLISH_RESULTS, publish_results_node)


    flow.set_entry_point(EXTRACT_PAPER_INFORMATION)


    flow.add_edge(EXTRACT_PAPER_INFORMATION, FILTER_PAPER_RELEVANCE)
    flow.add_edge(EXTRACT_PAPER_CONTENT, ANALYZE_PAPER)
    flow.add_edge(ANALYZE_PAPER, PUBLISH_RESULTS)


    flow.add_edge(PUBLISH_RESULTS, END)

   
    return flow.compile()

