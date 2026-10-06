from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class FailureCategory(str, Enum):
    WRONG_ENTITY = "wrong_entity"
    WRONG_SYSTEM_INSPECTED = "wrong_system_inspected"
    INSUFFICIENT_INVESTIGATION = "insufficient_investigation"
    POLICY_MISUNDERSTANDING = "policy_misunderstanding"
    INCORRECT_PERMISSION = "incorrect_permission"
    OVER_PERMISSIONING = "over_permissioning"
    UNDER_PERMISSIONING = "under_permissioning"
    UNNECESSARY_STATE_MODIFICATION = "unnecessary_state_modification"
    PREMATURE_COMPLETION = "premature_completion"
    FAILURE_TO_VERIFY = "failure_to_verify"
    INCORRECT_TICKET_HANDLING = "incorrect_ticket_handling"
    FAILURE_TO_ESCALATE = "failure_to_escalate"
    TOOL_MISUSE = "tool_misuse"
    PROVIDER_ERROR = "provider_error"
    AMBIGUOUS_REQUEST_FAILURE = "ambiguous_request_failure"
    NO_FAILURE = "none"


class ToolCallTrace(BaseModel):
    step: int
    tool_name: str
    arguments: Dict[str, Any]
    output: Dict[str, Any]
    error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: "")


class RuleCheckResult(BaseModel):
    rule_description: str
    passed: bool
    is_forbidden_check: bool
    weight: float
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)


class EvaluationReport(BaseModel):
    task_id: str
    task_title: str
    agent_id: str
    passed: bool
    total_score: float  # 0.0 to 1.0
    score_breakdown: Dict[str, float]
    rule_results: List[RuleCheckResult]
    tool_calls: List[ToolCallTrace]
    state_diff: Dict[str, Any] = Field(default_factory=dict)
    total_steps: int = 0
    read_tool_calls: int = 0
    mutation_tool_calls: int = 0
    termination_reason: str = ""
    failure_category: FailureCategory = FailureCategory.NO_FAILURE
    failure_explanation: str = ""
    duration_seconds: float = 0.0
