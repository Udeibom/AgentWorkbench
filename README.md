# AgentWorkbench

**A Local, Reproducible Benchmark and Failure-Analysis Platform for Evaluating Autonomous AI Agents on Stateful Enterprise & IT Service Workflows.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)

---

## Overview & Evaluation Philosophy

**AgentWorkbench** is a runnable evaluation environment designed to test autonomous AI agents on realistic enterprise IT Service Management (ITSM) workflows.

### Text Correctness vs. World-State Correctness
Most agent benchmarks evaluate models by judging what they **say** (text output / QA / explanations). 
In real-world enterprise operations, **text is cheap—state changes are what matter.**

An agent that writes a polite response explaining how to handle a department transfer, but fails to revoke legacy administrative access in the enterprise directory, has **failed**.

AgentWorkbench evaluates agents by:
1. Placing them in a synthetic, stateful SQLite enterprise environment (employees, roles, access groups, devices, tickets, policies).
2. Restricting interaction strictly to tool APIs (`grant_access`, `revoke_access`, `disable_account`, `assign_device`, `update_ticket`, etc.).
3. Capturing pre-task and post-task environment snapshots via a **State-Diff Engine**.
4. Inspecting the **final SQLite environment state** using a **Hidden Verifier** to verify required changes, forbidden changes, and state preservation.
5. Categorizing agent errors using a data-driven **Failure Taxonomy**.

---

## System Architecture

```text
Task / Ticket
      ↓
Stateful Enterprise Environment (SQLite)
      ↓
Restricted ToolRegistry
      ↓
Agent (ToolAgent)
      ↓
Groq Cloud LLM / Mock LLM
      ↓
Native Tool Calls (OpenAI-compatible protocol)
      ↓
Environment State Changes
      ↓
Agent Trajectory & State-Diff
      ↓
Hidden State Verifier
      ↓
Deterministic Score
      ↓
Failure Analysis Report
```

---

## Key Features

- **Offline-First Benchmark Engine**: The core environment, tasks, verifiers, scoring, and baselines run 100% locally and offline without requiring an LLM or internet connection.
- **Free Cloud LLM Integration (Groq)**: Supports autonomous agent experiments using free Groq-hosted LLMs (`GROQ_API_KEY`) via native OpenAI-compatible function calling.
- **Stateful SQLite Environment**: Seeded with synthetic employees, departments, hardware assets, security policies, and helpdesk tickets.
- **Restricted Tool API**: Agents interact exclusively through controlled tools; direct database manipulation is prohibited.
- **Hidden Verification**: Verifiers inspect underlying environment state post-execution.
- **Deterministic Scoring**: Transparent breakdown covering state correctness (70%), policy compliance (15%), safety preservation (10%), and ticket closure (5%).
- **Failure Taxonomy**: Automatically classifies failures (e.g. `OVER_PERMISSIONING`, `FAILURE_TO_ESCALATE`, `INSUFFICIENT_INVESTIGATION`).
- **Reproducible Evaluation**: Environment resets to a clean state before every task evaluation.
- **Dual Baselines**: Includes a deterministic **Scripted Oracle Agent** and a **Naïve Baseline Agent** to prove the benchmark detects shallow behavior.

---

## Quick Start

### 1. Installation

Clone the repository and install in editable mode:

```bash
git clone https://github.com/Udeibom/AgentWorkbench.git
cd AgentWorkbench

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .[dev]
```

### 2. Run the Benchmark Suite (Offline)

Run the full core benchmark suite using the deterministic baseline agent:

```bash
python -m agentworkbench benchmark --agent scripted
```

### 3. Run the Naïve Baseline Agent

Demonstrate how the benchmark catches shallow behavior (e.g. failing policy checks):

```bash
python -m agentworkbench benchmark --agent naive
```

### 4. Run a Specific Task

Run an individual task (e.g., department transfer permission reconciliation):

```bash
python -m agentworkbench run --task department_transfer_002 --agent scripted
```

### 5. Optional: Free Cloud LLM Experiments (Groq)

AgentWorkbench includes a Groq-backed tool-calling agent for live experiments. Because free-tier provider rate limits are external to the benchmark, deterministic offline agents are used for reproducible suite evaluation.

To run a live LLM experiment on a task:

```bash
# Set your free Groq API key
export GROQ_API_KEY="your_groq_api_key_here"
export GROQ_MODEL="openai/gpt-oss-20b"

# Run opt-in live smoke test
python -m agentworkbench smoke-test --agent groq

# Run single task experiment
python -m agentworkbench run --task account_lockout_006 --agent groq
```

---

## Sample Benchmark Output

```text
==================================================
          AgentWorkbench Evaluation Report        
==================================================
Tasks Evaluated: 11
Tasks Passed:    8 / 11 (72.7%)
Overall Score:   0.959

Task: department_transfer_002 (Department Transfer with Stale Permission Reconciliation)
Result: ✗ FAIL | Score: 0.85 | Steps: 7 (Read: 4, Mutate: 3)
Passed Rules:
  ✓ Employee emp-004 must be granted engineering-standard access
  ✓ Ticket tck-102 must be resolved
  ✓ Preservation of unrelated employee permissions
Failed Rules:
  ✗ Employee emp-004 legacy finance-admin access MUST be revoked (Access group 'finance-admin' STILL EXISTS for emp-004)
  ✗ Employee emp-004 legacy finance-standard access MUST be revoked (Access group 'finance-standard' STILL EXISTS for emp-004)
Failure Category: over_permissioning
Likely Issue:     Agent granted new role permissions but failed to revoke stale permissions inherited from previous department/role.
--------------------------------------------------
```

---

## Benchmark Tasks Overview

The `tasks/core/` directory contains 11 realistic IT workflows across 3 difficulty tiers:

| Task ID | Title | Difficulty | Tested Capability |
|---|---|---|---|
| `onboarding_001` | New Employee Provisioning | Easy | User activation, role entitlement, laptop assignment |
| `department_transfer_002` | Dept Transfer & Permission Cleanup | Medium | Dual-action grant & stale access revocation |
| `department_transfer_002_variant_ambiguous` | Dept Transfer (Ambiguous Wording) | Hard | Policy reconciliation under ambiguous wording |
| `offboarding_003` | Employee Departure Handling | Medium | Account termination, access wipe, device unassignment |
| `lost_device_004` | Stolen Laptop Incident Handling | Medium | Device status update, account suspension, incident log |
| `app_access_request_005` | Application Access Request | Easy | Direct entitlement granting |
| `account_lockout_006` | Account Lockout Reactivation | Easy | Account status unlock |
| `device_replacement_007` | Hardware Damage Replacement | Medium | Hardware asset decommissioning & re-issuance |
| `duplicate_ticket_008` | Duplicate Ticket Handling | Medium | Ticket linking, fulfillment, duplicate resolution |
| `contractor_policy_escalation_009` | Security Policy Enforcement | Hard | Identifying contractor restrictions & escalating |
| `ambiguous_transfer_010` | Ambiguous Transfer Investigation | Hard | Cross-system investigation & policy reconciliation |

---

## Testing

Run the full offline test suite:

```bash
pytest -q
```

All 18 unit and integration tests run offline without network requests or API keys.

---

## Documentation

- [`docs/benchmark-design.md`](docs/benchmark-design.md): Deep dive into evaluation philosophy, state-diffing, scoring math, failure taxonomy, and benchmark limitations.
- [`docs/demo.md`](docs/demo.md): 5-minute demonstration guide.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
