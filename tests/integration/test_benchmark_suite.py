import os
import pytest
from agentworkbench.tasks.task_loader import TaskRegistry
from agentworkbench.agents.scripted_baseline import ScriptedBaselineAgent
from agentworkbench.benchmark.runner import BenchmarkRunner


def test_integration_full_suite_run(tmp_path):
    output_dir = str(tmp_path / "reports")
    registry = TaskRegistry()
    runner = BenchmarkRunner(task_registry=registry, output_dir=output_dir)

    # 1. Run realistic baseline agent (demonstrates both passes and realistic failures)
    agent_realistic = ScriptedBaselineAgent(agent_id="baseline_realistic", mode="realistic")
    reports_realistic = runner.run_suite(agent_realistic, suite_name="core")

    assert len(reports_realistic) >= 10
    # Verify that JSON report files were persisted
    json_files = os.listdir(output_dir)
    assert len(json_files) >= 10

    # 2. Run perfect baseline agent (demonstrates 100% verifier pass)
    agent_perfect = ScriptedBaselineAgent(agent_id="baseline_perfect", mode="perfect")
    reports_perfect = runner.run_suite(agent_perfect, suite_name="core")

    perfect_passed = sum(1 for r in reports_perfect if r.passed)
    assert perfect_passed == len(reports_perfect)


def test_integration_single_task_end_to_end(tmp_path):
    output_dir = str(tmp_path / "reports")
    registry = TaskRegistry()
    runner = BenchmarkRunner(task_registry=registry, output_dir=output_dir)

    task = registry.get_task("onboarding_001")
    agent = ScriptedBaselineAgent(agent_id="baseline", mode="perfect")

    report = runner.run_task(task, agent)

    assert report.task_id == "onboarding_001"
    assert report.passed is True
    assert report.total_score >= 0.85
    assert len(report.tool_calls) > 0
    assert report.duration_seconds > 0
