import pytest
from agentworkbench.environment.db import SyntheticEnvironment
from agentworkbench.environment.fixtures import seed_default_fixture
from agentworkbench.api.tools import ToolRegistry


def test_tool_permissions_and_mutations():
    env = SyntheticEnvironment(":memory:")
    seed_default_fixture(env)
    tools = ToolRegistry(env)

    # 1. Read employee
    emp = tools.get_employee("emp-004")
    assert emp["id"] == "emp-004"

    # 2. Check access before grant
    access_before = tools.get_user_access("emp-004")
    groups_before = [a["access_group_id"] for a in access_before]
    assert "engineering-standard" not in groups_before

    # 3. Grant access
    res_grant = tools.grant_access("emp-004", "engineering-standard")
    assert res_grant["success"] is True

    access_after = tools.get_user_access("emp-004")
    groups_after = [a["access_group_id"] for a in access_after]
    assert "engineering-standard" in groups_after

    # 4. Revoke access
    res_revoke = tools.revoke_access("emp-004", "finance-admin")
    assert res_revoke["success"] is True

    access_final = tools.get_user_access("emp-004")
    groups_final = [a["access_group_id"] for a in access_final]
    assert "finance-admin" not in groups_final


def test_ticket_resolution_and_comments():
    env = SyntheticEnvironment(":memory:")
    seed_default_fixture(env)
    tools = ToolRegistry(env)

    # Add comment and resolve ticket
    res_comment = tools.add_ticket_comment("tck-101", "Testing comment logging.")
    assert res_comment["success"] is True

    res = tools.resolve_ticket("tck-101", "Resolution completed successfully.")
    assert res["success"] is True

    tck = tools.get_ticket("tck-101")
    assert tck["status"] == "resolved"
    assert len(tck["comments"]) >= 1
