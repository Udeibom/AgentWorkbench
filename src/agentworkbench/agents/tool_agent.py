import json
import uuid
from typing import List, Dict, Any, Optional
from agentworkbench.agents.base import BaseAgent
from agentworkbench.agents.providers import BaseLLMProvider, GroqProvider
from agentworkbench.models.task import TaskDefinition
from agentworkbench.api.tools import ToolRegistry


class ToolAgent(BaseAgent):
    """
    Autonomous multi-step tool-calling agent using native OpenAI/Groq tool-call messaging protocol.
    Iteratively queries tools, reasons over structured tool outputs, mutates environment state,
    and finishes when work is complete and verified.
    """

    def __init__(self, agent_id: str = "tool_agent", provider: Optional[BaseLLMProvider] = None, max_steps: int = 15):
        super().__init__(agent_id)
        self.provider = provider or GroqProvider()
        self.max_steps = max_steps
        self.last_termination_reason = ""
        self.step_history: List[Dict[str, Any]] = []

    def run(self, task: TaskDefinition, tools: ToolRegistry) -> str:
        self.step_history = []
        self.last_termination_reason = ""

        # Fetch initial ticket info
        ticket_info = tools.get_ticket(task.ticket_id)

        system_prompt = (
            "You are an autonomous IT support specialist operating inside an enterprise IT environment. "
            "You receive helpdesk tickets and interact exclusively via structured tool calls.\n"
            "INSTRUCTIONS:\n"
            "1. Investigate the ticket details, requester, target employee, current access, role, and corporate security policies using read tools.\n"
            "2. Determine the correct state modifications (grants, revocations, status updates, asset assignments).\n"
            "3. Execute required state changes via mutation tools.\n"
            "4. Verify your changes.\n"
            "5. Call 'resolve_ticket', 'escalate_ticket', or 'finish' when complete.\n"
            "6. Prefer the minimum sufficient investigation. Once you have the target employee's current access and the target role's default_access_groups, compare them directly and execute the required changes. Do not inspect individual access groups unless their metadata is necessary to determine policy compliance.\n"
            "7. Do not repeatedly inspect resources that are already represented in the information returned by another tool.\n"
            "8. After determining the required mutations, perform them before additional optional investigation.\n\n"
            "WORKFLOW FOR ACCESS/ROLE CHANGES:\n"
            "- Get the employee's current access.\n"
            "- Get the target role.\n"
            "- Compare current access against role.default_access_groups.\n"
            "- Grant missing required groups.\n"
            "- Revoke stale groups that should no longer remain.\n"
            "- Verify the resulting access.\n"
            "- Resolve the ticket.\n\n"
            "Do NOT guess IDs. Always inspect existing state first."
        )

        initial_user_msg = (
            f"New Ticket Assigned:\n"
            f"Ticket ID: {task.ticket_id}\n"
            f"Title: {task.title}\n"
            f"Description: {task.description}\n"
            f"Ticket Object: {json.dumps(ticket_info)}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": initial_user_msg}
        ]

        tool_defs = tools.get_tool_definitions()

        for step in range(1, self.max_steps + 1):
            decision = self.provider.generate(messages, tool_defs)
            self.step_history.append({"step": step, "decision": decision})

            if decision["type"] == "finish":
                self.last_termination_reason = decision.get("content", "Completed")
                return self.last_termination_reason

            elif decision["type"] == "error":
                self.last_termination_reason = f"Provider Error: {decision.get('error')}"
                return self.last_termination_reason

            elif decision["type"] == "tool_call":
                t_name = decision["tool_name"]
                t_args = decision.get("arguments", {})
                call_id = decision.get("tool_call_id", f"call_{uuid.uuid4().hex[:8]}")

                # 1. Add assistant tool_calls message to conversation history
                if "raw_message" in decision:
                    messages.append(decision["raw_message"])
                else:
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": call_id,
                                "type": "function",
                                "function": {
                                    "name": t_name,
                                    "arguments": json.dumps(t_args)
                                }
                            }
                        ]
                    })

                # 2. Execute tool against environment
                output = tools.execute_tool(t_name, t_args)

                # 3. Add native tool result message to conversation history
                messages.append({
                    "role": "tool",
                    "tool_call_id": call_id,
                    "name": t_name,
                    "content": json.dumps(output)
                })

                # 4. Termination checks
                if t_name == "finish":
                    self.last_termination_reason = t_args.get("reason", "Finished")
                    return self.last_termination_reason
                elif t_name == "resolve_ticket":
                    self.last_termination_reason = f"Resolved ticket {t_args.get('ticket_id')}"
                    return self.last_termination_reason
                elif t_name == "escalate_ticket":
                    self.last_termination_reason = f"Escalated ticket {t_args.get('ticket_id')}"
                    return self.last_termination_reason

        self.last_termination_reason = f"Reached maximum steps ({self.max_steps})"
        return self.last_termination_reason
