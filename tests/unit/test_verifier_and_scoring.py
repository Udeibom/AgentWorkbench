import pytest
from agentworkbench.environment.db import SyntheticEnvironment
from agentworkbench.environment.fixtures import seed_default_fixture
from agentworkbench.tasks.task_loader import TaskRegistry
from agentworkbench.verifier.hidden_verifier import HiddenVerifier
from agentworkbench.scoring.scoring_engine import ScoringEngine
from agentworkbench.analysis.failure_analyzer import FailureAnalyzer
from agentworkbench.models.evaluation import FailureCategory
from agentworkbench.api.tools import ToolRegistry


def test_task_loading():
    registry = TaskRegistry()
    tasks = registry.list_tasks()
    assert len(tasks) >= 10
    
    t1 = registry.get_task("onboarding_001")
    assert t1 is not None
    assert t1.task_id == "onboarding_001"


def test_verifier_success_and_scoring():
    env = SyntheticEnvironment(":memory:")
    seed_default_fixture(env)
    snapshot = env.capture_snapshot()
    tools = ToolRegistry(env)

    registry = TaskRegistry()
    task = registry.get_task("onboarding_001")

    # Perform required state changes manually
    tools.enable_account("emp-006")
    tools.grant_access("emp-006", "engineering-standard")
    tools.assign_device("dev-108", "emp-006")
    tools.resolve_ticket("tck-101", "Completed onboarding.")

    verifier = HiddenVerifier(env, snapshot)
    results = verifier.verify_task(task)
    
    score, passed, breakdown = ScoringEngine.calculate_score(task, results)
    assert score >= 0.80
    assert passed is True
    assert breakdown["state_correctness"] == 1.0


def test_verifier_forbidden_state_change_detection():
    env = SyntheticEnvironment(":memory:")
    seed_default_fixture(env)
    snapshot = env.capture_snapshot()
    tools = ToolRegistry(env)

    registry = TaskRegistry()
    task = registry.get_task("contractor_policy_escalation_009")

    # Violate security policy by granting restricted access to contractor
    tools.grant_access("emp-005", "prod-db-access")

    verifier = HiddenVerifier(env, snapshot)
    results = verifier.verify_task(task)

    score, passed, breakdown = ScoringEngine.calculate_score(task, results)
    assert passed is False

    cat, explanation = FailureAnalyzer.analyze_failure(task, results, tools.trace_history)
    assert cat in [FailureCategory.FAILURE_TO_ESCALATE, FailureCategory.OVER_PERMISSIONING]


def test_provider_error_failure_categorization():
    env = SyntheticEnvironment(":memory:")
    seed_default_fixture(env)
    snapshot = env.capture_snapshot()
    tools = ToolRegistry(env)

    registry = TaskRegistry()
    task = registry.get_task("onboarding_001")
    verifier = HiddenVerifier(env, snapshot)
    results = verifier.verify_task(task)

    cat, explanation = FailureAnalyzer.analyze_failure(
        task, results, tools.trace_history, termination_reason="Provider Error: HTTP 403 Rate Limit"
    )
    assert cat == FailureCategory.PROVIDER_ERROR
    assert "Provider Error: HTTP 403 Rate Limit" in explanation

