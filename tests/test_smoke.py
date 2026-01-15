import pytest
from unittest.mock import patch, MagicMock
from research_radar.workflow.graph import build_graph
from research_radar.workflow.state import WorkflowStatus

@pytest.fixture
def mock_initial_state():
    return {
        "workflow_id": "test-123",
        "paper_id": "2510.fake_paper",
        "metadata": None,
        "content": None,
        "status": WorkflowStatus.PENDING.value,
        "error": None,
        "required_keywords": ["LLM"], 
    }

@patch("research_radar.workflow.nodes.PaperMetadataExtractor")  
@patch("research_radar.workflow.nodes.PaperContentExtractor")  
@patch("research_radar.workflow.nodes.PaperRAGProcessor")  
def test_workflow_end_to_end_smoke(mock_rag, mock_content, mock_metadata, mock_initial_state):
    """
    Runs the full graph but MOCKS all external calls.
    """

    mock_metadata.return_value.extract_metadata.return_value = {
        "title": "Fake Paper Title",
        "authors": ["Dr. Test"],
        "date": "2025-01-01"
    }

    mock_content.return_value.extract_content.return_value = "# Fake Content\nThis is a test paper."

    rag_instance = mock_rag.return_value
    rag_instance.process_paper.return_value = "fake_hash_123"
    rag_instance.analyze_paper.return_value = {
        "analysis": {
            "summary": "AI is great.",
            "novelty": "Very high."
        }
    }

    print("\nRunning Smoke Test...")
    app = build_graph()
    result = app.invoke(mock_initial_state)

    print("Graph finished. Verifying...")
    assert result["status"] == WorkflowStatus.COMPLETED.value
    print("Test Passed!")