from enum import Enum
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class VerifierRuleType(str, Enum):
    CHECK_EMPLOYEE_STATUS = "check_employee_status"
    CHECK_EMPLOYEE_DEPARTMENT = "check_employee_department"
    CHECK_ACCESS_GRANTED = "check_access_granted"
    CHECK_ACCESS_REVOKED = "check_access_revoked"
    CHECK_DEVICE_ASSIGNMENT = "check_device_assignment"
    CHECK_DEVICE_STATUS = "check_device_status"
    CHECK_TICKET_STATUS = "check_ticket_status"
    CHECK_TICKET_COMMENT_CONTAINS = "check_ticket_comment_contains"
    CHECK_FORBIDDEN_ACCESS_GRANTED = "check_forbidden_access_granted"
    CHECK_UNRELATED_STATE_PRESERVED = "check_unrelated_state_preserved"


class VerifierRule(BaseModel):
    rule_type: VerifierRuleType
    description: str
    target_id: Optional[str] = None
    expected_value: Optional[Any] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    weight: float = 1.0
    is_forbidden_check: bool = False  # If True, failure indicates a forbidden change penalty


class ScoringConfig(BaseModel):
    state_correctness_weight: float = 0.70
    policy_compliance_weight: float = 0.15
    safety_preservation_weight: float = 0.10
    ticket_closure_weight: float = 0.05


class TaskDefinition(BaseModel):
    task_id: str
    title: str
    description: str
    ticket_id: str
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    tags: List[str] = Field(default_factory=list)
    initial_state_fixture: str = "default"  # Fixture seed name
    verifier_rules: List[VerifierRule] = Field(default_factory=list)
    scoring_config: ScoringConfig = Field(default_factory=ScoringConfig)
    known_failure_modes: List[str] = Field(default_factory=list)
    variant_id: Optional[str] = None
