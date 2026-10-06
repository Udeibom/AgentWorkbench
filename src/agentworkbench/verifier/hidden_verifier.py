from typing import List, Dict, Any, Tuple
from agentworkbench.environment.db import SyntheticEnvironment
from agentworkbench.models.task import TaskDefinition, VerifierRule, VerifierRuleType
from agentworkbench.models.evaluation import RuleCheckResult


class HiddenVerifier:
    """Inspects SQLite environment state after agent execution to verify outcome correctness."""

    def __init__(self, env: SyntheticEnvironment, initial_snapshot: Dict[str, List[Dict[str, Any]]]):
        self.env = env
        self.initial_snapshot = initial_snapshot

    def verify_task(self, task: TaskDefinition) -> List[RuleCheckResult]:
        results = []
        for rule in task.verifier_rules:
            res = self._check_rule(rule, task)
            results.append(res)
        return results

    def _check_rule(self, rule: VerifierRule, task: TaskDefinition) -> RuleCheckResult:
        rule_type = rule.rule_type

        if rule_type == VerifierRuleType.CHECK_EMPLOYEE_STATUS:
            return self._check_employee_status(rule)

        elif rule_type == VerifierRuleType.CHECK_EMPLOYEE_DEPARTMENT:
            return self._check_employee_department(rule)

        elif rule_type == VerifierRuleType.CHECK_ACCESS_GRANTED:
            return self._check_access_granted(rule)

        elif rule_type == VerifierRuleType.CHECK_ACCESS_REVOKED:
            return self._check_access_revoked(rule)

        elif rule_type == VerifierRuleType.CHECK_DEVICE_ASSIGNMENT:
            return self._check_device_assignment(rule)

        elif rule_type == VerifierRuleType.CHECK_DEVICE_STATUS:
            return self._check_device_status(rule)

        elif rule_type == VerifierRuleType.CHECK_TICKET_STATUS:
            return self._check_ticket_status(rule)

        elif rule_type == VerifierRuleType.CHECK_TICKET_COMMENT_CONTAINS:
            return self._check_ticket_comment_contains(rule)

        elif rule_type == VerifierRuleType.CHECK_FORBIDDEN_ACCESS_GRANTED:
            return self._check_forbidden_access_granted(rule)

        elif rule_type == VerifierRuleType.CHECK_UNRELATED_STATE_PRESERVED:
            return self._check_unrelated_state_preserved(rule, task)

        return RuleCheckResult(
            rule_description=rule.description,
            passed=False,
            is_forbidden_check=rule.is_forbidden_check,
            weight=rule.weight,
            message=f"Unknown rule type {rule_type}"
        )

    def _check_employee_status(self, rule: VerifierRule) -> RuleCheckResult:
        emp_id = rule.target_id
        expected = str(rule.expected_value).lower()
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT status FROM employees WHERE id = ?", (emp_id,))
            row = cursor.fetchone()
            actual = row["status"].lower() if row else "not_found"
            passed = (actual == expected)
            msg = f"Employee {emp_id} status is '{actual}' (expected '{expected}')"
            return RuleCheckResult(
                rule_description=rule.description,
                passed=passed,
                is_forbidden_check=rule.is_forbidden_check,
                weight=rule.weight,
                message=msg,
                details={"actual": actual, "expected": expected}
            )

    def _check_employee_department(self, rule: VerifierRule) -> RuleCheckResult:
        emp_id = rule.target_id
        expected = str(rule.expected_value)
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT department_id FROM employees WHERE id = ?", (emp_id,))
            row = cursor.fetchone()
            actual = row["department_id"] if row else "not_found"
            passed = (actual == expected)
            msg = f"Employee {emp_id} department is '{actual}' (expected '{expected}')"
            return RuleCheckResult(
                rule_description=rule.description,
                passed=passed,
                is_forbidden_check=rule.is_forbidden_check,
                weight=rule.weight,
                message=msg,
                details={"actual": actual, "expected": expected}
            )

    def _check_access_granted(self, rule: VerifierRule) -> RuleCheckResult:
        emp_id = rule.target_id
        grp_id = rule.params.get("access_group_id")
        with self.env.get_cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM employee_access WHERE employee_id = ? AND access_group_id = ?",
                (emp_id, grp_id)
            )
            found = cursor.fetchone() is not None
            msg = f"Access group '{grp_id}' {'IS' if found else 'IS NOT'} granted to {emp_id}"
            return RuleCheckResult(
                rule_description=rule.description,
                passed=found,
                is_forbidden_check=rule.is_forbidden_check,
                weight=rule.weight,
                message=msg,
                details={"employee_id": emp_id, "access_group_id": grp_id, "granted": found}
            )

    def _check_access_revoked(self, rule: VerifierRule) -> RuleCheckResult:
        emp_id = rule.target_id
        grp_id = rule.params.get("access_group_id")
        with self.env.get_cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM employee_access WHERE employee_id = ? AND access_group_id = ?",
                (emp_id, grp_id)
            )
            found = cursor.fetchone() is not None
            passed = not found
            msg = f"Access group '{grp_id}' {'STILL EXISTS' if found else 'REVOKED'} for {emp_id}"
            return RuleCheckResult(
                rule_description=rule.description,
                passed=passed,
                is_forbidden_check=rule.is_forbidden_check,
                weight=rule.weight,
                message=msg,
                details={"employee_id": emp_id, "access_group_id": grp_id, "revoked": passed}
            )

    def _check_device_assignment(self, rule: VerifierRule) -> RuleCheckResult:
        emp_id = rule.target_id
        with self.env.get_cursor() as cursor:
            cursor.execute(
                "SELECT id, status FROM devices WHERE assigned_to_employee_id = ? AND status = 'assigned'",
                (emp_id,)
            )
            rows = cursor.fetchall()
            passed = len(rows) > 0
            dev_ids = [r["id"] for r in rows]
            msg = f"Employee {emp_id} has assigned devices: {dev_ids}" if passed else f"Employee {emp_id} has NO assigned laptop"
            return RuleCheckResult(
                rule_description=rule.description,
                passed=passed,
                is_forbidden_check=rule.is_forbidden_check,
                weight=rule.weight,
                message=msg,
                details={"assigned_device_ids": dev_ids}
            )

    def _check_device_status(self, rule: VerifierRule) -> RuleCheckResult:
        dev_id = rule.target_id
        expected = rule.expected_value
        allowed_statuses = rule.params.get("allowed_statuses", [])
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT status FROM devices WHERE id = ?", (dev_id,))
            row = cursor.fetchone()
            actual = row["status"] if row else "not_found"
            if expected:
                passed = (actual == expected)
            elif allowed_statuses:
                passed = (actual in allowed_statuses)
            else:
                passed = False
            msg = f"Device {dev_id} status is '{actual}' (expected: {expected or allowed_statuses})"
            return RuleCheckResult(
                rule_description=rule.description,
                passed=passed,
                is_forbidden_check=rule.is_forbidden_check,
                weight=rule.weight,
                message=msg,
                details={"actual": actual, "expected": expected or allowed_statuses}
            )

    def _check_ticket_status(self, rule: VerifierRule) -> RuleCheckResult:
        tck_id = rule.target_id
        expected = rule.expected_value
        allowed_statuses = rule.params.get("allowed_statuses", [])
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT status FROM tickets WHERE id = ?", (tck_id,))
            row = cursor.fetchone()
            actual = row["status"] if row else "not_found"
            if expected:
                passed = (actual == expected)
            elif allowed_statuses:
                passed = (actual in allowed_statuses)
            else:
                passed = False
            msg = f"Ticket {tck_id} status is '{actual}' (expected: {expected or allowed_statuses})"
            return RuleCheckResult(
                rule_description=rule.description,
                passed=passed,
                is_forbidden_check=rule.is_forbidden_check,
                weight=rule.weight,
                message=msg,
                details={"actual": actual, "expected": expected or allowed_statuses}
            )

    def _check_ticket_comment_contains(self, rule: VerifierRule) -> RuleCheckResult:
        tck_id = rule.target_id
        kw = rule.params.get("keyword", "").lower()
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT content FROM ticket_comments WHERE ticket_id = ?", (tck_id,))
            comments = [r["content"].lower() for r in cursor.fetchall()]
            found = any(kw in c for c in comments)
            msg = f"Ticket {tck_id} comment contains keyword '{kw}' ({found})"
            return RuleCheckResult(
                rule_description=rule.description,
                passed=found,
                is_forbidden_check=rule.is_forbidden_check,
                weight=rule.weight,
                message=msg,
                details={"keyword": kw, "found": found}
            )

    def _check_forbidden_access_granted(self, rule: VerifierRule) -> RuleCheckResult:
        emp_id = rule.target_id
        grp_id = rule.params.get("access_group_id")
        with self.env.get_cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM employee_access WHERE employee_id = ? AND access_group_id = ?",
                (emp_id, grp_id)
            )
            found = cursor.fetchone() is not None
            passed = not found  # Forbidden check passes if NOT found!
            msg = f"Forbidden access '{grp_id}' was {'VIOLATED (granted)' if found else 'PRESERVED (not granted)'}"
            return RuleCheckResult(
                rule_description=rule.description,
                passed=passed,
                is_forbidden_check=True,
                weight=rule.weight,
                message=msg,
                details={"employee_id": emp_id, "access_group_id": grp_id, "violated": found}
            )

    def _check_unrelated_state_preserved(self, rule: VerifierRule, task: TaskDefinition) -> RuleCheckResult:
        current_snapshot = self.env.capture_snapshot()
        initial_emps = {e["id"]: e for e in self.initial_snapshot.get("employees", [])}
        current_emps = {e["id"]: e for e in current_snapshot.get("employees", [])}
        
        # Collect all employee IDs targeted by task rules
        target_emp_ids = set()
        if rule.target_id and rule.target_id.startswith("emp-"):
            target_emp_ids.add(rule.target_id)
        for r in task.verifier_rules:
            if r.target_id and r.target_id.startswith("emp-"):
                target_emp_ids.add(r.target_id)
            if r.params and "employee_id" in r.params:
                target_emp_ids.add(r.params["employee_id"])

        modified_unrelated = []
        for emp_id, initial_data in initial_emps.items():
            if emp_id in target_emp_ids:
                continue
            curr_data = current_emps.get(emp_id)
            if curr_data and curr_data != initial_data:
                if curr_data["status"] != initial_data["status"]:
                    modified_unrelated.append(f"Employee {emp_id} status changed to {curr_data['status']}")

        passed = len(modified_unrelated) == 0
        msg = "Unrelated employee states preserved cleanly" if passed else f"Unrelated states modified: {modified_unrelated}"
        return RuleCheckResult(
            rule_description=rule.description,
            passed=passed,
            is_forbidden_check=True,
            weight=rule.weight,
            message=msg,
            details={"unrelated_modifications": modified_unrelated}
        )
