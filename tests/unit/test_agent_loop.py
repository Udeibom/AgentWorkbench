import pytest
from agentworkbench.environment.db import SyntheticEnvironment
from agentworkbench.environment.fixtures import seed_default_fixture
from agentworkbench.tasks.task_loader import TaskRegistry
from agentworkbench.api.tools import ToolRegistry
from agentworkbench.agents.providers import MockLLMProvider
from agentworkbench.agents.tool_agent import ToolAgent
from agentworkbench.agents.naive_agent import NaiveAgent
from agentworkbench.benchmark.runner import BenchmarkRunner


def test_1_single_tool_call():
    env = SyntheticEnvironment(":memory:")
    seed_default_fixture(env)
    tools = ToolRegistry(env)
    task = TaskRegistry().get_task("onboarding_001")

    responses = [
        {"type": "tool_call", "tool_name": "get_employee", "arguments": {"employee_id": "emp-006"}},
        {"type": "finish", "content": "Done inspecting"}
    ]
    provider = MockLLMProvider(response_sequence=responses)
    agent = ToolAgent(agent_id="test_agent", provider=provider)

    res = agent.run(task, tools)
    assert res == "Done inspecting"
    agent_calls = [t for t in tools.trace_history if t.step > 1]
    assert len(agent_calls) == 1
    assert agent_calls[0].tool_name == "get_employee"


def test_2_multiple_tool_calls():
    env = SyntheticEnvironment(":memory:")
    seed_default_fixture(env)
    tools = ToolRegistry(env)
    task = TaskRegistry().get_task("onboarding_001")

    responses = [
        {"type": "tool_call", "tool_name": "get_employee", "arguments": {"employee_id": "emp-006"}},
        {"type": "tool_call", "tool_name": "get_role", "arguments": {"role_id": "role-eng-dev"}},
        {"type": "tool_call", "tool_name": "enable_account", "arguments": {"employee_id": "emp-006"}},
        {"type": "finish", "content": "Verified and completed"}
    ]
    provider = MockLLMProvider(response_sequence=responses)
    agent = ToolAgent(agent_id="test_agent", provider=provider)

    res = agent.run(task, tools)
    assert res == "Verified and completed"
    agent_calls = [t for t in tools.trace_history if t.step > 1]
    assert len(agent_calls) == 3
    assert agent_calls[2].tool_name == "enable_account"


def test_3_tool_error_recovery():
    env = SyntheticEnvironment(":memory:")
    seed_default_fixture(env)
    tools = ToolRegistry(env)
    task = TaskRegistry().get_task("onboarding_001")

    responses = [
        {"type": "tool_call", "tool_name": "get_employee", "arguments": {"employee_id": "invalid-id"}},
        {"type": "tool_call", "tool_name": "search_employees", "arguments": {"query": "David Miller"}},
        {"type": "finish", "content": "Recovered from error"}
    ]
    provider = MockLLMProvider(response_sequence=responses)
    agent = ToolAgent(agent_id="test_agent", provider=provider)

    res = agent.run(task, tools)
    assert res == "Recovered from error"
    agent_calls = [t for t in tools.trace_history if t.step > 1]
    assert len(agent_calls) == 2
    assert "error" in agent_calls[0].output


def test_4_invalid_model_action():
    env = SyntheticEnvironment(":memory:")
    seed_default_fixture(env)
    tools = ToolRegistry(env)
    task = TaskRegistry().get_task("onboarding_001")

    responses = [
        {"type": "tool_call", "tool_name": "non_existent_tool", "arguments": {}},
        {"type": "finish", "content": "Handled invalid action"}
    ]
    provider = MockLLMProvider(response_sequence=responses)
    agent = ToolAgent(agent_id="test_agent", provider=provider)

    res = agent.run(task, tools)
    assert res == "Handled invalid action"
    agent_calls = [t for t in tools.trace_history if t.step > 1]
    assert len(agent_calls) == 1
    assert "Unknown tool" in agent_calls[0].output["error"]


def test_5_maximum_step_protection():
    env = SyntheticEnvironment(":memory:")
    seed_default_fixture(env)
    tools = ToolRegistry(env)
    task = TaskRegistry().get_task("onboarding_001")

    responses = [{"type": "tool_call", "tool_name": "get_employee", "arguments": {"employee_id": "emp-006"}}] * 20
    provider = MockLLMProvider(response_sequence=responses)
    agent = ToolAgent(agent_id="test_agent", provider=provider, max_steps=5)

    res = agent.run(task, tools)
    assert "Reached maximum steps" in res
    agent_calls = [t for t in tools.trace_history if t.step > 1]
    assert len(agent_calls) == 5


def test_6_full_end_to_end_mock_run(tmp_path):
    output_dir = str(tmp_path / "reports")
    registry = TaskRegistry()
    runner = BenchmarkRunner(task_registry=registry, output_dir=output_dir)
    task = registry.get_task("onboarding_001")

    responses = [
        {"type": "tool_call", "tool_name": "get_employee", "arguments": {"employee_id": "emp-006"}},
        {"type": "tool_call", "tool_name": "enable_account", "arguments": {"employee_id": "emp-006"}},
        {"type": "tool_call", "tool_name": "grant_access", "arguments": {"employee_id": "emp-006", "access_group_id": "engineering-standard"}},
        {"type": "tool_call", "tool_name": "assign_device", "arguments": {"device_id": "dev-108", "employee_id": "emp-006"}},
        {"type": "tool_call", "tool_name": "resolve_ticket", "arguments": {"ticket_id": "tck-101", "resolution_summary": "Activated and assigned laptop."}}
    ]
    provider = MockLLMProvider(response_sequence=responses)
    agent = ToolAgent(agent_id="tool_agent_mock", provider=provider)

    report = runner.run_task(task, agent)

    assert report.task_id == "onboarding_001"
    assert report.passed is True
    assert report.total_score >= 0.85
    assert report.total_steps >= 6
    assert report.read_tool_calls >= 1
    assert report.mutation_tool_calls >= 4
    assert len(report.state_diff["access_changes"]) > 0


def test_7_naive_agent_fails_policy_task(tmp_path):
    output_dir = str(tmp_path / "reports")
    registry = TaskRegistry()
    runner = BenchmarkRunner(task_registry=registry, output_dir=output_dir)
    task = registry.get_task("contractor_policy_escalation_009")

    naive_agent = NaiveAgent()
    report = runner.run_task(task, naive_agent)

    # Naive agent blindly grants prod DB access to contractor and fails policy check!
    assert report.passed is False
    assert report.failure_category in ["failure_to_escalate", "over_permissioning"]


def test_8_groq_provider_user_agent_header():
    import json
    from unittest.mock import patch, MagicMock
    from agentworkbench.agents.providers import GroqProvider

    provider = GroqProvider(api_key="gsk_test_key")
    captured_req = None

    def fake_urlopen(req, timeout=15):
        nonlocal captured_req
        captured_req = req
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "choices": [{"message": {"content": "OK"}}]
        }).encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        res = provider.generate([{"role": "user", "content": "hi"}], [])
        assert res["type"] == "finish"
        assert captured_req is not None
        assert captured_req.get_header("User-agent") == "AgentWorkBench/1.0"

