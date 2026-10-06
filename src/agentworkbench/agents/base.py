from abc import ABC, abstractmethod
from typing import Dict, Any
from agentworkbench.models.task import TaskDefinition
from agentworkbench.api.tools import ToolRegistry


class BaseAgent(ABC):
    """Abstract interface for all agents evaluated on AgentWorkbench."""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id

    @abstractmethod
    def run(self, task: TaskDefinition, tools: ToolRegistry) -> str:
        """Executes the agent on the given task using available tools. Returns a final text response."""
        pass
