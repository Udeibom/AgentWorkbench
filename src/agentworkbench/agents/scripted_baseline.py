from agentworkbench.agents.base import BaseAgent
from agentworkbench.models.task import TaskDefinition
from agentworkbench.api.tools import ToolRegistry


class ScriptedBaselineAgent(BaseAgent):
    """
    Deterministic scripted baseline agent for AgentWorkbench.
    Runs without any external LLM service to guarantee reproducible execution.
    Can be configured in 'realistic' mode (where it makes realistic errors like missing revocation)
    or 'perfect' mode (where it executes ideal steps for all tasks).
    """

    def __init__(self, agent_id: str = "baseline", mode: str = "realistic"):
        super().__init__(agent_id)
        self.mode = mode

    def run(self, task: TaskDefinition, tools: ToolRegistry) -> str:
        tid = task.task_id

        # ---------------- Task 1: onboarding_001 ----------------
        if tid == "onboarding_001":
            tools.get_employee("emp-006")
            tools.enable_account("emp-006")
            tools.grant_access("emp-006", "engineering-standard")
            tools.grant_access("emp-006", "jira-developer")
            tools.grant_access("emp-006", "slack-general")
            tools.grant_access("emp-006", "vpn-employee")
            tools.assign_device("dev-108", "emp-006")
            tools.resolve_ticket("tck-101", "Activated David Miller, granted role access, and assigned laptop dev-108.")
            return "Provisioned onboarding employee and assigned laptop."

        # ---------------- Task 2: department_transfer_002 ----------------
        elif tid == "department_transfer_002" or tid == "department_transfer_002_variant_ambiguous":
            tools.get_employee("emp-004")
            tools.get_user_access("emp-004")
            tools.grant_access("emp-004", "engineering-standard")
            tools.grant_access("emp-004", "jira-developer")
            tools.grant_access("emp-004", "vpn-employee")
            
            if self.mode == "realistic":
                # Realistic failure: Baseline agent grants new access but forgets to revoke legacy finance permissions!
                pass
            else:
                # Perfect mode cleans up legacy access
                tools.revoke_access("emp-004", "finance-admin")
                tools.revoke_access("emp-004", "finance-standard")

            tools.resolve_ticket("tck-102", "Granted Engineering access groups for Jane Doe.")
            return "Updated transfer access for employee."

        # ---------------- Task 3: offboarding_003 ----------------
        elif tid == "offboarding_003":
            tools.get_employee("emp-007")
            tools.get_user_access("emp-007")
            tools.disable_account("emp-007", status="terminated")
            tools.revoke_access("emp-007", "slack-general")
            tools.revoke_access("emp-007", "vpn-employee")
            tools.assign_device("dev-106", None)  # Unassign device
            tools.update_device_status("dev-106", "in_stock")
            tools.resolve_ticket("tck-103", "Offboarded Eve Adams, revoked access, and returned laptop to stock.")
            return "Offboarding complete."

        # ---------------- Task 4: lost_device_004 ----------------
        elif tid == "lost_device_004":
            tools.get_device("dev-103")
            tools.update_device_status("dev-103", "stolen")
            tools.disable_account("emp-003", status="suspended")
            tools.add_ticket_comment("tck-104", "SECURITY INCIDENT: Corporate ThinkPad dev-103 marked stolen; employee account suspended per policy pol-incident-01.")
            tools.resolve_ticket("tck-104", "Stolen device isolated and incident logged.")
            return "Incident response executed."

        # ---------------- Task 5: app_access_request_005 ----------------
        elif tid == "app_access_request_005":
            tools.get_employee("emp-002")
            tools.grant_access("emp-002", "vpn-employee")
            tools.resolve_ticket("tck-105", "Granted Corporate VPN access to Bob Builder.")
            return "Granted VPN access."

        # ---------------- Task 6: account_lockout_006 ----------------
        elif tid == "account_lockout_006":
            tools.get_employee("emp-009")
            tools.enable_account("emp-009")
            tools.resolve_ticket("tck-106", "Reactivated Frank Wright's account after manager identity confirmation.")
            return "Unlocked account."

        # ---------------- Task 7: device_replacement_007 ----------------
        elif tid == "device_replacement_007":
            tools.get_device("dev-101")
            tools.assign_device("dev-101", None)
            tools.update_device_status("dev-101", "decommissioned")
            tools.assign_device("dev-108", "emp-001")
            tools.resolve_ticket("tck-107", "Decommissioned dev-101 due to battery swelling and assigned replacement dev-108 to Alice Vance.")
            return "Replaced damaged laptop."

        # ---------------- Task 8: duplicate_ticket_008 ----------------
        elif tid == "duplicate_ticket_008":
            tools.get_ticket("tck-108")
            tools.get_ticket("tck-108b")
            tools.grant_access("emp-005", "jira-developer")
            tools.add_ticket_comment("tck-108b", "Duplicate request resolved under main ticket tck-108.")
            tools.resolve_ticket("tck-108b", "Closed as duplicate of tck-108.")
            tools.resolve_ticket("tck-108", "Granted Jira developer access to Charlie Smith.")
            return "Resolved duplicate tickets."

        # ---------------- Task 9: contractor_policy_escalation_009 ----------------
        elif tid.startswith("contractor_policy_escalation_009"):
            tools.get_employee("emp-005")
            tools.get_policy("pol-contractor-01")
            
            if self.mode == "realistic":
                # Baseline error: Naively grants access instead of recognizing security policy constraint!
                tools.grant_access("emp-005", "prod-db-access")
                tools.resolve_ticket("tck-109", "Granted prod-db-access.")
                return "Granted requested access."
            else:
                # Correct behavior: Escalate ticket due to contractor policy violation
                tools.escalate_ticket("tck-109", "Contractor Charlie Smith requested production database access without logged manager approval. Policy pol-contractor-01 requires manager authorization.")
                return "Escalated ticket due to policy restriction."

        # ---------------- Task 10: ambiguous_transfer_010 ----------------
        elif tid == "ambiguous_transfer_010":
            tools.get_employee("emp-004")
            tools.get_role("role-eng-dev")
            tools.get_policy("pol-access-01")
            tools.grant_access("emp-004", "engineering-standard")
            tools.grant_access("emp-004", "jira-developer")
            tools.grant_access("emp-004", "vpn-employee")
            tools.revoke_access("emp-004", "finance-admin")
            tools.revoke_access("emp-004", "finance-standard")
            tools.resolve_ticket("tck-110", "Reconciled access permissions for Jane Doe following transfer to Engineering.")
            return "Reconciled transfer access."

        # Fallback for unknown tasks
        tools.resolve_ticket(task.ticket_id, "Completed request.")
        return "Executed fallback task handling."
