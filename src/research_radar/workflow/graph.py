from langgraph.graph import StateGraph
from research_radar.workflow.state import WorkflowState
from research_radar.workflow.node_types import EXTRACT_PAPER_INFORMATION
from research_radar.workflow.nodes import extract_paper_information_node


def build_graph():
    flow = StateGraph(WorkflowState)

    flow.add_node(EXTRACT_PAPER_INFORMATION, extract_paper_information_node)

    flow.set_entry_point(EXTRACT_PAPER_INFORMATION)

    return flow.compile()
