import argparse
import sys
import os
from agentworkbench.tasks.task_loader import TaskRegistry
from agentworkbench.agents.scripted_baseline import ScriptedBaselineAgent
from agentworkbench.agents.naive_agent import NaiveAgent
from agentworkbench.agents.tool_agent import ToolAgent
from agentworkbench.agents.providers import GroqProvider, MockLLMProvider
from agentworkbench.benchmark.runner import BenchmarkRunner


def get_agent_instance(agent_name: str):
    if agent_name in ["scripted", "baseline"]:
        return ScriptedBaselineAgent(agent_id="scripted_baseline", mode="realistic")
    elif agent_name == "baseline_perfect":
        return ScriptedBaselineAgent(agent_id="baseline_perfect", mode="perfect")
    elif agent_name == "naive":
        return NaiveAgent(agent_id="naive_baseline")
    elif agent_name == "groq":
        return ToolAgent(agent_id="tool_agent_groq", provider=GroqProvider())
    elif agent_name == "mock":
        return ToolAgent(agent_id="tool_agent_mock", provider=MockLLMProvider())
    else:
        raise ValueError(f"Unknown agent: {agent_name}")


def parse_args():
    parser = argparse.ArgumentParser(description="AgentWorkbench: Benchmark for evaluating autonomous AI agents.")
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    # Command: list-tasks
    subparsers.add_parser("list-tasks", help="List all benchmark tasks.")

    # Command: run
    run_parser = subparsers.add_parser("run", help="Run a specific task or suite.")
    run_parser.add_argument("--task", type=str, help="Task ID to execute.")
    run_parser.add_argument("--suite", type=str, default="core", help="Task suite to run (default: core).")
    run_parser.add_argument("--agent", type=str, default="scripted", help="Agent implementation (scripted, naive, groq, mock).")
    run_parser.add_argument("--output-dir", type=str, default="reports", help="Output reports directory.")

    # Command: benchmark
    bm_parser = subparsers.add_parser("benchmark", help="Run full benchmark suite.")
    bm_parser.add_argument("--agent", type=str, default="scripted", help="Agent implementation (scripted, naive, groq, mock).")
    bm_parser.add_argument("--suite", type=str, default="core", help="Task suite name.")
    bm_parser.add_argument("--output-dir", type=str, default="reports", help="Output reports directory.")

    # Command: smoke-test
    smoke_parser = subparsers.add_parser("smoke-test", help="Opt-in live API integration smoke test.")
    smoke_parser.add_argument("--agent", type=str, default="groq", help="Target API provider (default: groq).")

    # Global options for top-level backward compatibility
    parser.add_argument("--task", type=str, help="Specific task ID to run.")
    parser.add_argument("--suite", type=str, help="Task suite to run.")
    parser.add_argument("--agent", type=str, default="scripted", help="Agent implementation.")
    parser.add_argument("--output-dir", type=str, default="reports", help="Output reports directory.")

    return parser.parse_args()


def handle_smoke_test(agent_name: str):
    print("==================================================")
    print("          AgentWorkbench Live Smoke Test          ")
    print("==================================================")
    if agent_name == "groq":
        key = os.getenv("GROQ_API_KEY")
        if not key:
            print("ERROR: GROQ_API_KEY environment variable is not set.")
            print("To run the opt-in live Groq smoke test, set GROQ_API_KEY in your environment:")
            print("  export GROQ_API_KEY=\"your_groq_api_key\"")
            sys.exit(1)

        model_name = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        print(f"Executing miniature tool-calling loop using Groq model '{model_name}'...")
        
        task_registry = TaskRegistry()
        runner = BenchmarkRunner(task_registry=task_registry)
        task = task_registry.get_task("app_access_request_005")  # Small simple task
        agent = ToolAgent(agent_id="tool_agent_groq", provider=GroqProvider(), max_steps=5)

        try:
            report = runner.run_task(task, agent)
            print(f"\nTask: {report.task_id}")
            print(f"Pass Status: {'✓ PASS' if report.passed else '✗ FAIL'}")
            print(f"Total Score: {report.total_score}")
            print(f"Tool Steps Executed: {report.total_steps}")
            print(f"Termination Reason: {report.termination_reason}")
            if report.passed:
                print("\n✓ Live Groq tool-calling smoke test PASSED successfully!")
            else:
                print(f"\n✗ Smoke test executed but task failed: {report.failure_explanation}")
        except Exception as e:
            print(f"\n✗ Live Groq smoke test FAILED with exception: {e}")


def main():
    args = parse_args()
    task_registry = TaskRegistry()

    if args.command == "list-tasks":
        tasks = task_registry.list_tasks()
        print("\nAvailable AgentWorkbench Benchmark Tasks:")
        print("--------------------------------------------------")
        for t in tasks:
            print(f"ID: {t.task_id:<35} | Tier: {t.difficulty.value:<6} | Title: {t.title}")
        print("--------------------------------------------------")
        return

    elif args.command == "smoke-test":
        handle_smoke_test(args.agent)
        return

    # Determine command action
    cmd = args.command or "run"
    agent_name = getattr(args, "agent", "scripted")
    output_dir = getattr(args, "output_dir", "reports")
    task_id = getattr(args, "task", None)
    suite_name = getattr(args, "suite", "core")

    try:
        agent = get_agent_instance(agent_name)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    runner = BenchmarkRunner(task_registry=task_registry, output_dir=output_dir)

    if task_id:
        task = task_registry.get_task(task_id)
        if not task:
            print(f"Task '{task_id}' not found in registry.")
            sys.exit(1)
        print(f"Running task '{task_id}' with agent '{agent.agent_id}'...")
        report = runner.run_task(task, agent)
        runner.print_summary_report([report])
    else:
        print(f"Running benchmark suite '{suite_name}' with agent '{agent.agent_id}'...")
        reports = runner.run_suite(agent, suite_name=suite_name)
        runner.print_summary_report(reports)


if __name__ == "__main__":
    main()
