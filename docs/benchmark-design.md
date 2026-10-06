# AgentWorkbench: Benchmark Design & Evaluation Architecture

## 1. Executive Summary & Design Philosophy

AgentWorkbench is a local, reproducible evaluation and failure-analysis benchmark designed to assess autonomous AI agents on realistic enterprise business and IT operations workflows.

Modern LLM benchmark practices often evaluate agents by examining their generated text responses (e.g., QA accuracy or conversational plausibility). However, in real-world IT service management (ITSM) and enterprise operations:
- **An agent is not useful because it outputs a convincing narrative.**
- **An agent is useful only when it reliably transforms the operational environment into the correct target state through state-changing tools.**

AgentWorkbench enforces a strict **World-State Evaluation paradigm**:
1. Agents operate inside a synthetic, stateful SQLite enterprise environment through a restricted Tool API.
2. Direct database access is blocked; agents must investigate, reason, and take action via tools.
3. Upon task completion, a **Hidden Verifier** inspects the underlying SQLite database state via a **State-Diff Engine** to verify required mutations, forbidden actions, and preservation of unrelated records.
4. Deterministic scoring and data-driven failure taxonomy classify root-cause failures.
5. The benchmark infrastructure runs 100% locally and offline without requiring an LLM or paid APIs, while optional LLM experiments use free Groq-hosted inference (`GROQ_API_KEY`) via native function calling.

---

## 2. Realism Criteria & Workflow Mapping

Tasks in AgentWorkbench are grounded in standard enterprise ITSM practices (e.g., ITIL Service Desk, IAM, ISO 27001 Access Controls).

### Task Realism Principles:
- **Plausible Requesters & Context**: Tickets mirror genuine helpdesk requests (e.g., onboarding, department transfers, stolen laptops, contractor access requests).
- **Legitimate Investigation Requirement**: Tasks cannot be solved by blindly acting on the initial ticket text. The agent must query employee status, role definitions, access groups, or security policies.
- **Side-Effect Verification**: Operations in real enterprise systems carry security side-effects. For instance, transferring an employee from Finance to Engineering requires both granting new Engineering permissions AND revoking stale Finance administrative access.
- **Policy Enforcement & Escalation**: Not all user requests should be executed. Requests violating security policies (e.g., contractor requesting production DB access without manager approval) must be escalated or denied.

---

## 3. Task Difficulty & Families

AgentWorkbench organizes tasks across 3 difficulty tiers:

| Tier | Characteristics | Example Workflows |
|---|---|---|
| **Easy** | Single-step/direct lookup, straightforward access grant or account activation. | `onboarding_001`, `app_access_request_005`, `account_lockout_006` |
| **Medium** | Multi-system state changes, hardware asset re-assignment, duplicate ticket resolution. | `offboarding_003`, `lost_device_004`, `device_replacement_007`, `duplicate_ticket_008` |
| **Hard** | Cross-system permission reconciliation, ambiguous task formulation, strict security policy escalation. | `department_transfer_002`, `contractor_policy_escalation_009`, `ambiguous_transfer_010` |

---

## 4. Hidden Verifier Architecture & State-Diff Engine

### Why Deterministic Verification Over LLM-as-a-Judge?
Using an LLM as a judge for evaluating state-changing agents introduces non-determinism, prompt sensitivity, hallucinated judgments, and high API cost. 
AgentWorkbench uses **deterministic code verifiers** inspecting SQLite table state via `StateDiffEngine`:
- **Required State Changes**: Asserts target attributes (e.g. `employee.status == 'active'`).
- **Forbidden State Changes**: Detects unauthorized permission grants or policy breaches.
- **Preservation of Unrelated State**: Compares pre-task and post-task environment snapshots to penalize agents that modify unrelated entities.

### Scoring Formula:
The overall task score $S \in [0.0, 1.0]$ is calculated via weighted category breakdowns:
$$\text{Score} = w_{\text{state}} \cdot C_{\text{state}} + w_{\text{policy}} \cdot C_{\text{policy}} + w_{\text{safety}} \cdot C_{\text{safety}} + w_{\text{closure}} \cdot C_{\text{closure}}$$

Where default weights are:
- State Correctness ($w_{\text{state}} = 0.70$)
- Policy Compliance ($w_{\text{policy}} = 0.15$)
- Safety & Preservation ($w_{\text{safety}} = 0.10$)
- Ticket Closure ($w_{\text{closure}} = 0.05$)

---

## 5. Failure Taxonomy

When a task fails or receives partial credit, AgentWorkbench categorizes the failure into a structured taxonomy:

- `WRONG_ENTITY`: Agent acted on the wrong user or asset.
- `WRONG_SYSTEM_INSPECTED`: Inspected irrelevant tools/resources.
- `INSUFFICIENT_INVESTIGATION`: Acted without inspecting policies or existing state.
- `POLICY_MISUNDERSTANDING`: Violated security policy rules.
- `OVER_PERMISSIONING`: Granted excess or stale permissions.
- `UNDER_PERMISSIONING`: Failed to grant required role access.
- `PREMATURE_COMPLETION`: Resolved ticket without performing state changes.
- `FAILURE_TO_ESCALATE`: Granted forbidden access instead of escalating.
- `TOOL_MISUSE`: Provided invalid arguments to tool APIs.

---

## 6. Evaluation Risks & Research Limitations

1. **Reward Hacking**: An agent might learn to call `grant_access` for all groups. The verifier guards against this via `check_forbidden_access_granted` and `check_unrelated_state_preserved`.
2. **Benchmark Leakage**: Task definitions, expected state rules, and verifier logic are strictly separated from tool outputs exposed to the agent.
3. **Simulator-to-Real-World Gap**: While SQLite synthetically models enterprise database state, real-world ITSM tools (ServiceNow, Okta, Jira) involve network latency, API rate limits, and asynchronous approval flows. AgentWorkbench can be extended with async tool adapters to narrow this gap.
