from langgraph.graph import StateGraph, END
from research_radar.workflow.state import WorkflowState
from research_radar.workflow.node_types import (
    EXTRACT_PAPER_INFORMATION,
    FILTER_PAPER_RELEVANCE,
    EXTRACT_PAPER_CONTENT,
    ANALYZE_PAPER,
    PUBLISH_RESULTS,

)

from research_radar.workflow.nodes import (
    extract_paper_information_node,
    filter_paper_relevance_node,
    extract_paper_content_node,
    analyze_paper_node,
    publish_results_node,

)



def route_relevance_check(state: WorkflowState) -> str:

    """
    Conditional edge router based on the relevance_result.
    """

    if state.get("relevance_result"):
        # Paper is relevant, continue to content extraction
        return EXTRACT_PAPER_CONTENT

    else:
        # Paper is NOT relevant, end the workflow
        return END



def build_graph():
    flow = StateGraph(WorkflowState)


    flow.add_node(EXTRACT_PAPER_INFORMATION, extract_paper_information_node)
    flow.add_node(FILTER_PAPER_RELEVANCE, filter_paper_relevance_node)
    flow.add_node(EXTRACT_PAPER_CONTENT, extract_paper_content_node)
    flow.add_node(ANALYZE_PAPER, analyze_paper_node)
    flow.add_node(PUBLISH_RESULTS, publish_results_node)


    flow.set_entry_point(EXTRACT_PAPER_INFORMATION)



# --- Define Edges ---

    # 1. After initial extraction, go to the new filter node
    flow.add_edge(EXTRACT_PAPER_INFORMATION, FILTER_PAPER_RELEVANCE)

    # 2. After filtering, use a conditional edge
    flow.add_conditional_edges(
        FILTER_PAPER_RELEVANCE,
        route_relevance_check,

        {
            EXTRACT_PAPER_CONTENT: EXTRACT_PAPER_CONTENT, # If relevant, go to content extraction
            END: END,                                      # If NOT relevant, end the workflow

        },

    )



    # 3. The rest of the workflow is sequential
    flow.add_edge(EXTRACT_PAPER_CONTENT, ANALYZE_PAPER)
    flow.add_edge(ANALYZE_PAPER, PUBLISH_RESULTS)



    # 4. Final step

    flow.add_edge(PUBLISH_RESULTS, END)

   

    # --------------------

    return flow.compile()

