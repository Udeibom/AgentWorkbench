import os
import yaml
from typing import List, Dict, Any, Optional
from agentworkbench.models.task import TaskDefinition, VerifierRule, ScoringConfig, DifficultyLevel, VerifierRuleType
from agentworkbench.environment.db import SyntheticEnvironment


class TaskRegistry:
    """Loads and manages task definitions for AgentWorkbench."""

    def __init__(self, tasks_dir: Optional[str] = None):
        if tasks_dir is None:
            # Default to tasks/core relative to project root or package
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            tasks_dir = os.path.join(base, "tasks", "core")
        self.tasks_dir = tasks_dir
        self.tasks: Dict[str, TaskDefinition] = {}
        self.load_all_tasks()

    def load_all_tasks(self):
        if not os.path.exists(self.tasks_dir):
            return
        for fname in os.listdir(self.tasks_dir):
            if fname.endswith(".yaml") or fname.endswith(".yml"):
                filepath = os.path.join(self.tasks_dir, fname)
                task_def = self.load_task_from_file(filepath)
                self.tasks[task_def.task_id] = task_def

    def load_task_from_file(self, filepath: str) -> TaskDefinition:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        
        # Convert verifier rules
        rules = []
        for r in data.get("verifier_rules", []):
            rule_type = VerifierRuleType(r["rule_type"])
            rules.append(
                VerifierRule(
                    rule_type=rule_type,
                    description=r.get("description", ""),
                    target_id=r.get("target_id"),
                    expected_value=r.get("expected_value"),
                    params=r.get("params", {}),
                    weight=r.get("weight", 1.0),
                    is_forbidden_check=r.get("is_forbidden_check", False)
                )
            )

        scoring_dict = data.get("scoring_config", {})
        scoring_config = ScoringConfig(**scoring_dict) if scoring_dict else ScoringConfig()

        return TaskDefinition(
            task_id=data["task_id"],
            title=data["title"],
            description=data["description"],
            ticket_id=data["ticket_id"],
            difficulty=DifficultyLevel(data.get("difficulty", "medium")),
            tags=data.get("tags", []),
            initial_state_fixture=data.get("initial_state_fixture", "default"),
            verifier_rules=rules,
            scoring_config=scoring_config,
            known_failure_modes=data.get("known_failure_modes", []),
            variant_id=data.get("variant_id")
        )

    def get_task(self, task_id: str) -> Optional[TaskDefinition]:
        return self.tasks.get(task_id)

    def list_tasks(self) -> List[TaskDefinition]:
        return list(self.tasks.values())
