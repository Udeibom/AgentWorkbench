from typing import List, Dict, Any, Tuple
from agentworkbench.models.task import TaskDefinition
from agentworkbench.models.evaluation import FailureCategory, RuleCheckResult, ToolCallTrace


class FailureAnalyzer:
    """Analyzes failed verifier rules and tool trace history to classify root cause failure taxonomy."""

    @staticmethod
    def analyze_failure(
        task: TaskDefinition,
        rule_results: List[RuleCheckResult],
        tool_traces: List[ToolCallTrace],
        termination_reason: str = ""
    ) -> Tuple[FailureCategory, str]:
        
        failed_rules = [r for r in rule_results if not r.passed]
        if not failed_rules:
            return FailureCategory.NO_FAILURE, "All verifier checks passed successfully."

        if termination_reason.lower().startswith("provider error:"):
            return (
                FailureCategory.PROVIDER_ERROR,
                f"Agent execution was interrupted by the model provider before the task was completed. {termination_reason}"
            )

        # Analyze tool trace patterns
        tool_names = [t.tool_name for t in tool_traces]
        had_errors = any(t.error is not None for t in tool_traces)

        # 1. Check if agent performed NO investigation tools before modifying state
        investigation_tools = {"get_employee", "search_employees", "get_user_access", "get_role", "get_policy", "search_policies", "get_ticket"}
        read_calls = [t for t in tool_traces if t.tool_name in investigation_tools]
        
        # 2. Check specific rule failure patterns
        failed_descriptions = [r.rule_description.lower() for r in failed_rules]
        failed_messages = [r.message.lower() for r in failed_rules]

        # Check for forbidden access / escalation failures
        if any("prod-db-access" in m or "forbidden access" in m for m in failed_messages):
            if any("escalated" in d or "escalate" in d for d in failed_descriptions):
                return (
                    FailureCategory.FAILURE_TO_ESCALATE,
                    "Agent granted unauthorized restricted access directly instead of recognizing security policy restrictions and escalating the ticket."
                )
            return (
                FailureCategory.OVER_PERMISSIONING,
                "Agent granted a forbidden access group, violating corporate security boundaries."
            )

        # Check for escalation missing
        if any("status is 'open'" in m or "status is 'in_progress'" in m for m in failed_messages):
            if task.task_id.startswith("contractor_policy_escalation"):
                return (
                    FailureCategory.FAILURE_TO_ESCALATE,
                    "Agent failed to escalate ticket when encountering contractor security policy restrictions."
                )

        # Check for legacy permission revocation failure (stale permissions retained)
        if any("revoked" in d or "legacy" in d for d in failed_descriptions):
            if len(read_calls) <= 1:
                return (
                    FailureCategory.INSUFFICIENT_INVESTIGATION,
                    "Agent handled the request without sufficiently inspecting existing permissions or role policies to identify stale access requiring cleanup."
                )
            if "grant_access" in tool_names:
                return (
                    FailureCategory.OVER_PERMISSIONING,
                    "Agent granted new access but failed to revoke stale permissions required by the target role or department."
                )
            return (
                FailureCategory.INSUFFICIENT_INVESTIGATION,
                "Agent inspected the environment but did not perform the required permission changes before termination."
            )

        # Check for missing laptop assignment or device status update
        if any("laptop" in d or "device" in d for d in failed_descriptions):
            if "assign_device" not in tool_names and "update_device_status" not in tool_names:
                return (
                    FailureCategory.UNDER_PERMISSIONING if "onboard" in task.task_id else FailureCategory.INSUFFICIENT_INVESTIGATION,
                    "Agent omitted required hardware asset assignment/status update in the environment."
                )

        # Check for account status / employee status failure
        if any("status should be updated to 'active'" in d or "terminated" in d or "suspended" in d for d in failed_descriptions):
            return (
                FailureCategory.INSUFFICIENT_INVESTIGATION,
                "Agent failed to update employee lifecycle status (active/suspended/terminated) in accordance with the requested workflow."
            )

        # Check for tool misuse errors
        if had_errors:
            return (
                FailureCategory.TOOL_MISUSE,
                "Agent encountered tool execution errors during task resolution."
            )

        # Check for premature ticket resolution without state change
        if any("ticket" in d for d in failed_descriptions) and len(failed_rules) > 1:
            return (
                FailureCategory.PREMATURE_COMPLETION,
                "Agent closed or updated ticket prematurely without making the required underlying environment state modifications."
            )

        # Generic fallback
        first_fail = failed_rules[0]
        return (
            FailureCategory.POLICY_MISUNDERSTANDING,
            f"Agent failed verifier rule: '{first_fail.rule_description}'. Details: {first_fail.message}"
        )
