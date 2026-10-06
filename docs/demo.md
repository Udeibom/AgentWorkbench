# AgentWorkbench Demonstration Guide

This guide walks through running and evaluating **AgentWorkbench** in under 5 minutes.

---

## Step 1: Run the Automated Test Suite

Verify that all unit, state-diff, hidden verifier, and multi-step tool loop tests pass offline:

```bash
source .venv/bin/activate
pytest -v
```

---

## Step 2: List Benchmark Tasks

View the 11 tasks across Easy, Medium, and Hard difficulty tiers:

```bash
python -m agentworkbench list-tasks
```

---

## Step 3: Run the Scripted Baseline (Oracle Agent)

Run the full core benchmark suite using the deterministic scripted baseline:

```bash
python -m agentworkbench benchmark --agent scripted
```

Output highlights:
- Overall score and task pass rate.
- Passed vs failed verifier rules.
- Structured failure analysis for realistic baseline errors.

---

## Step 4: Run the Naïve Baseline Agent (Shallow Agent)

Run the naive agent to see how AgentWorkbench catches shallow, non-investigative behavior:

```bash
python -m agentworkbench benchmark --agent naive
```

Observe:
- The Naïve agent fails policy-sensitive tasks (e.g., `contractor_policy_escalation_009`) because it blindly grants requested permissions without checking policies.
- The Naïve agent fails permission reconciliation tasks (`department_transfer_002`) because it forgets to clean up stale legacy permissions.

---

## Step 5: Run a Single Policy-Sensitive Task

Run contractor policy escalation using the Naïve agent vs Scripted agent:

```bash
# Naive agent (Fails policy)
python -m agentworkbench run --task contractor_policy_escalation_009 --agent naive

# Scripted agent (Passes policy)
python -m agentworkbench run --task contractor_policy_escalation_009 --agent baseline_perfect
```

---

## Step 6: Inspect Trajectory & State-Diff JSON Reports

Inspect the generated machine-readable report JSON files in `reports/`:

```bash
cat reports/onboarding_001_scripted_baseline_report.json
```

Key sections in JSON report:
1. `score_breakdown`: Weighted category breakdown (state correctness, policy compliance, safety preservation, ticket closure).
2. `state_diff`: Exact database mutations (employee status, access granted/revoked, device assignments).
3. `tool_calls`: Complete step-by-step trajectory trace.
4. `failure_category`: Root-cause taxonomy classification.

---

## Step 7: (Optional) Opt-In Live Groq API Smoke Test

If you have a free Groq API key (`GROQ_API_KEY`), test the live tool-calling adapter:

```bash
export GROQ_API_KEY="your-groq-api-key"
python -m agentworkbench smoke-test --agent groq
```
