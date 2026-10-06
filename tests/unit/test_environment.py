import pytest
from agentworkbench.environment.db import SyntheticEnvironment
from agentworkbench.environment.fixtures import seed_default_fixture


def test_environment_initialization_and_reset():
    env = SyntheticEnvironment(":memory:")
    seed_default_fixture(env)

    snapshot = env.capture_snapshot()
    assert len(snapshot["employees"]) > 0
    assert len(snapshot["departments"]) > 0
    assert len(snapshot["access_groups"]) > 0
    assert len(snapshot["policies"]) > 0

    env.reset_db()
    empty_snapshot = env.capture_snapshot()
    assert len(empty_snapshot["employees"]) == 0
    assert len(empty_snapshot["departments"]) == 0


def test_task_isolation():
    env1 = SyntheticEnvironment(":memory:")
    seed_default_fixture(env1)

    env2 = SyntheticEnvironment(":memory:")
    seed_default_fixture(env2)

    # Mutate env1
    with env1.get_cursor() as cursor:
        cursor.execute("UPDATE employees SET status = 'terminated' WHERE id = 'emp-001'")

    # env2 should be completely isolated and unaffected
    with env2.get_cursor() as cursor:
        cursor.execute("SELECT status FROM employees WHERE id = 'emp-001'")
        row = cursor.fetchone()
        assert row["status"] == "active"
