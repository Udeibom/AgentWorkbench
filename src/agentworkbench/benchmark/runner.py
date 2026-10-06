import time
import os
import json
from typing import List, Dict, Any, Optional
from agentworkbench.environment.db import SyntheticEnvironment
from agentworkbench.environment.fixtures import seed_default_fixture
from agentworkbench.tasks.task_loader import TaskRegistry
from agentworkbench.api.tools import ToolRegistry
from agentworkbench.verifier.hidden_verifier import HiddenVerifier
from agentworkbench.verifier.state_diff import StateDiffEngine
from agentworkbench.scoring.scoring_engine import ScoringEngine
from agentworkbench.analysis.failure_analyzer import FailureAnalyzer
from agentworkbench.agents.base import BaseAgent
from agentworkbench.agents.scripted_baseline import ScriptedBaselineAgent
from agentworkbench.agents.naive_agent import NaiveAgent
from agentworkbench.agents.tool_agent import ToolAgent
from agentworkbench.agents.providers import GroqProvider, MockLLMProvider
from agentworkbench.models.task import TaskDefinition
from agentworkbench.models.evaluation import EvaluationReport


class BenchmarkRunner:
    """Orchestrates benchmark task evaluation, state isolation, scoring, state-diffing, and report generation."""

    def __init__(self, task_registry: Optional[TaskRegistry] = None, output_dir: str = "reports"):
        self.task_registry = task_registry or TaskRegistry()
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def run_task(self, task: TaskDefinition, agent: BaseAgent) -> EvaluationReport:
        # 1. Initialize isolated in-memory environment
        env = SyntheticEnvironment(":memory:")
        seed_default_fixture(env)

        # 2. Capture initial state snapshot before agent execution
        initial_snapshot = env.capture_snapshot()

        # 3. Create tool registry bound to environment
        tools = ToolRegistry(env)

        # 4. Execute agent on task
        start_time = time.time()
        agent_error = None
        try:
            agent_res = agent.run(task, tools)
        except Exception as e:
            agent_error = str(e)
            agent_res = f"Exception: {str(e)}"
        duration = round(time.time() - start_time, 4)

        # 5. Capture final environment state and compute state diff
        final_snapshot = env.capture_snapshot()
        state_diff = StateDiffEngine.compute_diff(initial_snapshot, final_snapshot)

        # 6. Count read vs mutation tool calls
        read_tools = {"get_employee", "search_employees", "get_department", "get_role", "get_user_access", "get_access_group", "get_resource", "search_resources", "get_device", "search_devices", "get_ticket", "search_tickets", "get_policy", "search_policies"}
        read_count = sum(1 for t in tools.trace_history if t.tool_name in read_tools)
        mutation_count = len(tools.trace_history) - read_count

        # 7. Run hidden verifier on final environment state
        verifier = HiddenVerifier(env, initial_snapshot)
        rule_results = verifier.verify_task(task)

        # 8. Calculate score
        total_score, passed, score_breakdown = ScoringEngine.calculate_score(task, rule_results)

        # 9. Analyze failures
        term_reason = getattr(agent, "last_termination_reason", str(agent_res))
        failure_category, failure_explanation = FailureAnalyzer.analyze_failure(
            task, rule_results, tools.trace_history, term_reason
        )
        if agent_error:
            failure_explanation = f"Agent Exception: {agent_error}. {failure_explanation}"

        # 10. Assemble structured EvaluationReport
        report = EvaluationReport(
            task_id=task.task_id,
            task_title=task.title,
            agent_id=agent.agent_id,
            passed=passed,
            total_score=total_score,
            score_breakdown=score_breakdown,
            rule_results=rule_results,
            tool_calls=tools.trace_history,
            state_diff=state_diff,
            total_steps=len(tools.trace_history),
            read_tool_calls=read_count,
            mutation_tool_calls=mutation_count,
            termination_reason=term_reason,
            failure_category=failure_category,
            failure_explanation=failure_explanation,
            duration_seconds=duration
        )

        # 11. Save machine-readable JSON report
        report_file = os.path.join(self.output_dir, f"{task.task_id}_{agent.agent_id}_report.json")
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))

        return report

    def run_suite(self, agent: BaseAgent, suite_name: str = "core") -> List[EvaluationReport]:
        tasks = self.task_registry.list_tasks()
        reports = []
        for task in tasks:
            report = self.run_task(task, agent)
            reports.append(report)
        return reports

    @staticmethod
    def print_summary_report(reports: List[EvaluationReport]):
        total = len(reports)
        passed_count = sum(1 for r in reports if r.passed)
        avg_score = round(sum(r.total_score for r in reports) / total, 3) if total > 0 else 0.0

        print("\n==================================================")
        print("          AgentWorkbench Evaluation Report        ")
        print("==================================================")
        print(f"Tasks Evaluated: {total}")
        print(f"Tasks Passed:    {passed_count} / {total} ({round(passed_count/total*100, 1)}%)")
        print(f"Overall Score:   {avg_score}\n")

        for r in reports:
            status_symbol = "✓ PASS" if r.passed else "✗ FAIL"
            print(f"Task: {r.task_id} ({r.task_title})")
            print(f"Result: {status_symbol} | Score: {r.total_score} | Steps: {r.total_steps} (Read: {r.read_tool_calls}, Mutate: {r.mutation_tool_calls})")
            
            print("Passed Rules:")
            for rule in r.rule_results:
                if rule.passed:
                    print(f"  ✓ {rule.rule_description}")
            
            failed_rules = [rule for rule in r.rule_results if not rule.passed]
            if failed_rules:
                print("Failed Rules:")
                for rule in failed_rules:
                    print(f"  ✗ {rule.rule_description} ({rule.message})")

            if not r.passed:
                print(f"Failure Category: {r.failure_category.value}")
                print(f"Likely Issue:     {r.failure_explanation}")
            print("-" * 50)
