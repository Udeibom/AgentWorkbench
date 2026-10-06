from agentworkbench.agents.base import BaseAgent
from agentworkbench.models.task import TaskDefinition
from agentworkbench.api.tools import ToolRegistry


class NaiveAgent(BaseAgent):
    """
    Shallow Naïve Baseline Agent (Baseline B).
    Blindly performs requested access grants/actions literally mentioned in helpdesk tickets
    without inspecting existing permissions, verifying role standards, or checking security policies.
    
    Used as a baseline to prove that AgentWorkbench penalizes shallow, non-investigative behavior.
    """

    def __init__(self, agent_id: str = "naive_baseline"):
        super().__init__(agent_id)

    def run(self, task: TaskDefinition, tools: ToolRegistry) -> str:
        ticket = tools.get_ticket(task.ticket_id)
        desc = ticket.get("description", "").lower()
        target_emp = ticket.get("target_employee_id") or ticket.get("requester_employee_id")

        # Naively grant any mentioned access group literally
        if "engineering-standard" in desc or "engineering" in desc:
            tools.grant_access(target_emp, "engineering-standard")
        if "jira-developer" in desc or "jira" in desc:
            tools.grant_access(target_emp, "jira-developer")
        if "vpn-employee" in desc or "vpn" in desc:
            tools.grant_access(target_emp, "vpn-employee")
        if "prod-db-access" in desc or "production database" in desc:
            # Blindly grants restricted access without checking contractor security policy!
            tools.grant_access(target_emp, "prod-db-access")

        # Blindly resolves ticket without checking stale permissions or verifying
        tools.resolve_ticket(task.ticket_id, "Naively executed requested ticket instructions.")
        return "Naively executed request."
