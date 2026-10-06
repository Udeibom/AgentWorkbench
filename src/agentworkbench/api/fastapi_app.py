from fastapi import FastAPI, HTTPException
from typing import List, Optional
from agentworkbench.tasks.task_loader import TaskRegistry
from agentworkbench.agents.scripted_baseline import ScriptedBaselineAgent
from agentworkbench.benchmark.runner import BenchmarkRunner

app = FastAPI(
    title="AgentWorkbench API",
    description="REST API for executing and scoring autonomous AI agent benchmark tasks.",
    version="0.1.0"
)

task_registry = TaskRegistry()
runner = BenchmarkRunner(task_registry=task_registry)


@app.get("/")
def read_root():
    return {"status": "ok", "app": "AgentWorkbench", "tasks_count": len(task_registry.list_tasks())}


@app.get("/tasks")
def list_tasks():
    return [t.model_dump() for t in task_registry.list_tasks()]


@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    task = task_registry.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task.model_dump()


@app.post("/run/{task_id}")
def run_task(task_id: str, agent_mode: str = "realistic"):
    task = task_registry.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    agent = ScriptedBaselineAgent(agent_id=f"baseline_{agent_mode}", mode=agent_mode)
    report = runner.run_task(task, agent)
    return report.model_dump()
