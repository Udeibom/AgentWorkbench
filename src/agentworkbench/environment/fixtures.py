import json
from typing import Dict, Any
from agentworkbench.environment.db import SyntheticEnvironment


def seed_default_fixture(env: SyntheticEnvironment):
    """Seeds the synthetic company database with a rich, realistic IT environment."""
    env.reset_db()
    with env.get_cursor() as cursor:
        # 1. Departments
        cursor.executemany(
            "INSERT INTO departments (id, name, head_employee_id) VALUES (?, ?, ?)",
            [
                ("dept-eng", "Engineering", "emp-008"),
                ("dept-fin", "Finance", "emp-002"),
                ("dept-hr", "Human Resources", "emp-003"),
                ("dept-it", "IT Support", "emp-001"),
                ("dept-sales", "Sales", "emp-007"),
            ]
        )

        # 2. Roles
        cursor.executemany(
            "INSERT INTO roles (id, title, department_id, default_access_groups_json) VALUES (?, ?, ?, ?)",
            [
                ("role-eng-dev", "Software Engineer", "dept-eng", json.dumps(["engineering-standard", "jira-developer", "slack-general", "vpn-employee"])),
                ("role-eng-sr", "Senior Engineer", "dept-eng", json.dumps(["engineering-standard", "engineering-admin", "jira-developer", "slack-general", "vpn-employee"])),
                ("role-fin-analyst", "Financial Analyst", "dept-fin", json.dumps(["finance-standard", "slack-general", "vpn-employee"])),
                ("role-fin-mgr", "Finance Manager", "dept-fin", json.dumps(["finance-standard", "finance-admin", "slack-general", "vpn-employee"])),
                ("role-hr-spec", "HR Specialist", "dept-hr", json.dumps(["hr-confidential", "slack-general", "vpn-employee"])),
                ("role-it-spec", "IT Support Specialist", "dept-it", json.dumps(["it-admin", "slack-general", "vpn-employee"])),
                ("role-sales-exec", "Sales Executive", "dept-sales", json.dumps(["slack-general", "vpn-employee"])),
            ]
        )

        # 3. Access Groups
        cursor.executemany(
            "INSERT INTO access_groups (id, name, description, requires_approval, allowed_employment_types_json) VALUES (?, ?, ?, ?, ?)",
            [
                ("engineering-standard", "Engineering Standard Access", "Standard code repositories and internal docs", 0, json.dumps(["full_time", "contractor", "intern"])),
                ("engineering-admin", "Engineering Admin Access", "CI/CD administration and server deployment", 1, json.dumps(["full_time"])),
                ("finance-standard", "Finance Standard Access", "Financial reporting tools and expense portals", 0, json.dumps(["full_time"])),
                ("finance-admin", "Finance Admin Access", "Bank accounts, ledger modification, payroll", 1, json.dumps(["full_time"])),
                ("hr-confidential", "HR Confidential Data", "Employee records and salary information", 1, json.dumps(["full_time"])),
                ("it-admin", "IT System Administration", "Identity provider, endpoint management, asset control", 1, json.dumps(["full_time"])),
                ("slack-general", "Slack Workspace Access", "Company-wide instant messaging", 0, json.dumps(["full_time", "contractor", "intern"])),
                ("jira-developer", "Jira Developer Workspace", "Issue tracker and project boards", 0, json.dumps(["full_time", "contractor", "intern"])),
                ("prod-db-access", "Production Database Access", "Read-write access to production SQL database", 1, json.dumps(["full_time"])),
                ("vpn-employee", "Corporate VPN Access", "Remote access to corporate network", 0, json.dumps(["full_time", "contractor"])),
            ]
        )

        # 4. Resources
        cursor.executemany(
            "INSERT INTO resources (id, name, resource_type, sensitivity_level, access_group_id) VALUES (?, ?, ?, ?, ?)",
            [
                ("res-github", "GitHub Enterprise Org", "repo", "medium", "engineering-standard"),
                ("res-proddb", "Production PostgreSQL DB", "database", "critical", "prod-db-access"),
                ("res-ledger", "Financial Ledger Portal", "software", "high", "finance-admin"),
                ("res-workday", "Workday HR Platform", "software", "high", "hr-confidential"),
                ("res-jira", "Jira Workspace", "software", "low", "jira-developer"),
                ("res-slack", "Slack Workspace", "software", "low", "slack-general"),
            ]
        )

        # 5. Employees
        cursor.executemany(
            "INSERT INTO employees (id, email, full_name, department_id, role_id, employment_type, status, manager_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("emp-001", "alice.vance@company.com", "Alice Vance", "dept-it", "role-it-spec", "full_time", "active", None, "2024-01-10T08:00:00Z"),
                ("emp-002", "bob.builder@company.com", "Bob Builder", "dept-fin", "role-fin-mgr", "full_time", "active", None, "2024-01-15T08:00:00Z"),
                ("emp-003", "carol.danvers@company.com", "Carol Danvers", "dept-hr", "role-hr-spec", "full_time", "active", None, "2024-02-01T08:00:00Z"),
                ("emp-004", "jane.doe@company.com", "Jane Doe", "dept-eng", "role-eng-dev", "full_time", "active", "emp-008", "2024-03-01T08:00:00Z"), # Transferred from Fin to Eng
                ("emp-005", "charlie.smith@company.com", "Charlie Smith", "dept-eng", "role-eng-dev", "contractor", "active", "emp-008", "2024-04-01T08:00:00Z"), # Contractor
                ("emp-006", "david.miller@company.com", "David Miller", "dept-eng", "role-eng-dev", "full_time", "onboarding", "emp-008", "2024-10-01T08:00:00Z"), # New Hire
                ("emp-007", "eve.adams@company.com", "Eve Adams", "dept-sales", "role-sales-exec", "full_time", "active", None, "2024-05-01T08:00:00Z"), # Pending Offboard
                ("emp-008", "grace.hopper@company.com", "Grace Hopper", "dept-eng", "role-eng-sr", "full_time", "active", None, "2023-11-01T08:00:00Z"),
                ("emp-009", "frank.wright@company.com", "Frank Wright", "dept-sales", "role-sales-exec", "full_time", "suspended", None, "2024-06-01T08:00:00Z"), # Locked out
            ]
        )

        # 6. Employee Access (Current permissions)
        cursor.executemany(
            "INSERT INTO employee_access (employee_id, access_group_id, granted_at, granted_by) VALUES (?, ?, ?, ?)",
            [
                # Alice (IT Admin)
                ("emp-001", "it-admin", "2024-01-10T08:00:00Z", "system"),
                ("emp-001", "slack-general", "2024-01-10T08:00:00Z", "system"),

                # Bob (Fin Manager)
                ("emp-002", "finance-standard", "2024-01-15T08:00:00Z", "system"),
                ("emp-002", "finance-admin", "2024-01-15T08:00:00Z", "system"),
                ("emp-002", "slack-general", "2024-01-15T08:00:00Z", "system"),

                # Carol (HR)
                ("emp-003", "hr-confidential", "2024-02-01T08:00:00Z", "system"),
                ("emp-003", "slack-general", "2024-02-01T08:00:00Z", "system"),

                # Jane (Transferred to Eng, but STILL HAS legacy finance-standard & finance-admin access!)
                ("emp-004", "finance-standard", "2024-03-01T08:00:00Z", "system"),
                ("emp-004", "finance-admin", "2024-03-01T08:00:00Z", "system"),
                ("emp-004", "slack-general", "2024-03-01T08:00:00Z", "system"),

                # Charlie (Contractor Eng)
                ("emp-005", "engineering-standard", "2024-04-01T08:00:00Z", "system"),
                ("emp-005", "slack-general", "2024-04-01T08:00:00Z", "system"),

                # Eve (Offboard target)
                ("emp-007", "slack-general", "2024-05-01T08:00:00Z", "system"),
                ("emp-007", "vpn-employee", "2024-05-01T08:00:00Z", "system"),

                # Grace (Sr Dev)
                ("emp-008", "engineering-standard", "2023-11-01T08:00:00Z", "system"),
                ("emp-008", "engineering-admin", "2023-11-01T08:00:00Z", "system"),
                ("emp-008", "jira-developer", "2023-11-01T08:00:00Z", "system"),
                ("emp-008", "slack-general", "2023-11-01T08:00:00Z", "system"),
                ("emp-008", "vpn-employee", "2023-11-01T08:00:00Z", "system"),

                # Frank (Suspended)
                ("emp-009", "slack-general", "2024-06-01T08:00:00Z", "system"),
            ]
        )

        # 7. Devices
        cursor.executemany(
            "INSERT INTO devices (id, serial_number, model, device_type, assigned_to_employee_id, status) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("dev-101", "SN-LAP-101", "MacBook Pro 16", "laptop", "emp-001", "assigned"),
                ("dev-102", "SN-LAP-102", "MacBook Pro 14", "laptop", "emp-002", "assigned"),
                ("dev-103", "SN-LAP-103", "ThinkPad X1", "laptop", "emp-003", "assigned"),
                ("dev-104", "SN-LAP-104", "MacBook Pro 14", "laptop", "emp-004", "assigned"),
                ("dev-105", "SN-LAP-105", "ThinkPad T14", "laptop", "emp-005", "assigned"),
                ("dev-106", "SN-LAP-106", "Dell XPS 15", "laptop", "emp-007", "assigned"), # Eve's device
                ("dev-107", "SN-LAP-107", "MacBook Pro 16", "laptop", "emp-008", "assigned"),
                ("dev-108", "SN-LAP-108", "MacBook Air M2", "laptop", None, "in_stock"),
                ("dev-109", "SN-LAP-109", "MacBook Air M2", "laptop", None, "in_stock"),
                ("dev-110", "SN-LAP-110", "ThinkPad T14", "laptop", None, "in_stock"),
                ("dev-111", "SN-LAP-111", "Dell XPS 13", "laptop", "emp-009", "assigned"), # Frank's device
            ]
        )

        # 8. Tickets
        cursor.executemany(
            "INSERT INTO tickets (id, title, description, requester_employee_id, target_employee_id, status, priority, assigned_to, tags_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("tck-101", "New Hire Provisioning - David Miller", "David Miller started today as Software Engineer in Engineering. Activate account, grant role access, assign laptop.", "emp-003", "emp-006", "open", "high", None, json.dumps(["onboarding"]), "2024-10-05T08:00:00Z", "2024-10-05T08:00:00Z"),
                ("tck-102", "Role Transition - Jane Doe", "Jane Doe transferred from Finance to Engineering. Please update her access permissions for her new role as Software Engineer.", "emp-008", "emp-004", "open", "medium", None, json.dumps(["transfer"]), "2024-10-05T08:05:00Z", "2024-10-05T08:05:00Z"),
                ("tck-103", "Employee Offboarding - Eve Adams", "Eve Adams in Sales departed the company today. Execute complete offboarding checklist.", "emp-003", "emp-007", "open", "high", None, json.dumps(["offboarding"]), "2024-10-05T08:10:00Z", "2024-10-05T08:10:00Z"),
                ("tck-104", "URGENT: Stolen Device Reported", "Carol Danvers reported her corporate ThinkPad X1 (dev-103) stolen from vehicle.", "emp-003", "emp-003", "open", "urgent", None, json.dumps(["incident", "stolen"]), "2024-10-05T08:15:00Z", "2024-10-05T08:15:00Z"),
                ("tck-105", "Application Access Request - VPN", "Bob Builder requires Corporate VPN Access (vpn-employee) for remote work.", "emp-002", "emp-002", "open", "low", None, json.dumps(["access_request"]), "2024-10-05T08:20:00Z", "2024-10-05T08:20:00Z"),
                ("tck-106", "Account Lockout - Frank Wright", "Frank Wright locked out after password retries. Identity verified by Sales Director.", "emp-009", "emp-009", "open", "medium", None, json.dumps(["account_lockout"]), "2024-10-05T08:25:00Z", "2024-10-05T08:25:00Z"),
                ("tck-107", "Hardware Replacement - Alice Vance", "Alice Vance laptop dev-101 has swollen batteries. Decommission dev-101 and assign replacement laptop.", "emp-001", "emp-001", "open", "medium", None, json.dumps(["hardware"]), "2024-10-05T08:30:00Z", "2024-10-05T08:30:00Z"),
                ("tck-108", "Jira Access Request - Charlie Smith", "Charlie Smith requested Jira Developer access (jira-developer).", "emp-005", "emp-005", "open", "medium", None, json.dumps(["access_request"]), "2024-10-05T08:35:00Z", "2024-10-05T08:35:00Z"),
                ("tck-108b", "Duplicate Jira Request - Charlie Smith", "Duplicate ticket opened for Charlie Smith Jira Developer access.", "emp-005", "emp-005", "open", "low", None, json.dumps(["duplicate"]), "2024-10-05T08:36:00Z", "2024-10-05T08:36:00Z"),
                ("tck-109", "Access Request - Production DB", "Charlie Smith (emp-005) requested Production Database Access (prod-db-access).", "emp-005", "emp-005", "open", "medium", None, json.dumps(["access_request"]), "2024-10-05T08:40:00Z", "2024-10-05T08:40:00Z"),
                ("tck-110", "Ambiguous Transfer - Jane Doe", "Jane Doe moved to Engineering. Fix her access according to standard company guidelines.", "emp-008", "emp-004", "open", "medium", None, json.dumps(["transfer", "ambiguous"]), "2024-10-05T08:45:00Z", "2024-10-05T08:45:00Z"),
            ]
        )

        # 9. Policies
        cursor.executemany(
            "INSERT INTO policies (id, title, content, category) VALUES (?, ?, ?, ?)",
            [
                ("pol-access-01", "Access Management Policy", "Employees transitioning between departments must have access rights updated within 24 hours. Legacy access belonging exclusively to the previous role MUST be revoked immediately upon role transition.", "access"),
                ("pol-contractor-01", "Contractor Security Restrictions", "Contractors are strictly prohibited from holding Production Database Access (prod-db-access) or Engineering Admin Access unless explicit written manager approval is logged in the ticket. Requests without logged approval must be escalated or denied.", "security"),
                ("pol-offboard-01", "Employee Offboarding Procedure", "Upon employee departure, the account status must be set to 'terminated', all granted access groups must be revoked, and assigned hardware assets must be updated to status 'in_stock' or 'decommissioned'.", "hr_security"),
                ("pol-incident-01", "Lost or Stolen Asset Handling", "If a corporate device is reported lost or stolen, its status must be immediately updated to 'lost' or 'stolen', the assigned employee's account temporarily set to 'suspended', and an incident comment added to the ticket.", "incident"),
                ("pol-onboard-01", "New Employee Provisioning Standard", "New employees must be activated (status set to 'active'), assigned default access groups corresponding to their role, and assigned an available in_stock laptop device.", "onboarding"),
            ]
        )
