from enum import Enum
from typing import Optional, Dict
from typing_extensions import TypedDict


class WorkflowStatus(str, Enum):
    """Enum representing possible workflow statuses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WorkflowState(TypedDict):
    """
    Represents the state of a workflow
    """

    workflow_id: str
    paper_id: str
    metadata: Optional[Dict]
    content: Optional[str]
    status: WorkflowStatus
    error: Optional[str]
