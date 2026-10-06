import sqlite3
import json
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager


CREATE_TABLES_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS departments (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    head_employee_id TEXT
);

CREATE TABLE IF NOT EXISTS roles (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    department_id TEXT NOT NULL,
    default_access_groups_json TEXT NOT NULL DEFAULT '[]',
    FOREIGN KEY (department_id) REFERENCES departments(id)
);

CREATE TABLE IF NOT EXISTS employees (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    department_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    employment_type TEXT NOT NULL DEFAULT 'full_time',
    status TEXT NOT NULL DEFAULT 'active',
    manager_id TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES departments(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

CREATE TABLE IF NOT EXISTS access_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    requires_approval BOOLEAN NOT NULL DEFAULT 0,
    allowed_employment_types_json TEXT NOT NULL DEFAULT '["full_time", "contractor", "intern"]'
);

CREATE TABLE IF NOT EXISTS employee_access (
    employee_id TEXT NOT NULL,
    access_group_id TEXT NOT NULL,
    granted_at TEXT NOT NULL,
    granted_by TEXT NOT NULL DEFAULT 'system',
    PRIMARY KEY (employee_id, access_group_id),
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (access_group_id) REFERENCES access_groups(id)
);

CREATE TABLE IF NOT EXISTS resources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    sensitivity_level TEXT NOT NULL DEFAULT 'medium',
    access_group_id TEXT NOT NULL,
    FOREIGN KEY (access_group_id) REFERENCES access_groups(id)
);

CREATE TABLE IF NOT EXISTS devices (
    id TEXT PRIMARY KEY,
    serial_number TEXT UNIQUE NOT NULL,
    model TEXT NOT NULL,
    device_type TEXT NOT NULL,
    assigned_to_employee_id TEXT,
    status TEXT NOT NULL DEFAULT 'in_stock',
    FOREIGN KEY (assigned_to_employee_id) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    requester_employee_id TEXT NOT NULL,
    target_employee_id TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    priority TEXT NOT NULL DEFAULT 'medium',
    assigned_to TEXT,
    tags_json TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (requester_employee_id) REFERENCES employees(id),
    FOREIGN KEY (target_employee_id) REFERENCES employees(id)
);

CREATE TABLE IF NOT EXISTS ticket_comments (
    id TEXT PRIMARY KEY,
    ticket_id TEXT NOT NULL,
    author TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id)
);

CREATE TABLE IF NOT EXISTS policies (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    category TEXT NOT NULL
);
"""


class SyntheticEnvironment:
    """Manages the SQLite synthetic company environment for AgentWorkbench."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._conn: Optional[sqlite3.Connection] = None
        self.init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            if self._conn is None:
                self._conn = sqlite3.connect(":memory:", check_same_thread=False)
                self._conn.row_factory = sqlite3.Row
            return self._conn
        else:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            return conn

    @contextmanager
    def get_cursor(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def init_db(self):
        with self.get_cursor() as cursor:
            cursor.executescript(CREATE_TABLES_SQL)

    def reset_db(self):
        with self.get_cursor() as cursor:
            tables = [
                "ticket_comments", "tickets", "devices", "resources",
                "employee_access", "access_groups", "employees",
                "roles", "departments", "policies"
            ]
            for table in tables:
                cursor.execute(f"DELETE FROM {table}")

    def capture_snapshot(self) -> Dict[str, List[Dict[str, Any]]]:
        """Captures complete environment state for verification comparison."""
        snapshot = {}
        tables = [
            "departments", "roles", "employees", "access_groups",
            "employee_access", "resources", "devices", "tickets",
            "ticket_comments", "policies"
        ]
        with self.get_cursor() as cursor:
            for table in tables:
                cursor.execute(f"SELECT * FROM {table}")
                rows = [dict(r) for r in cursor.fetchall()]
                snapshot[table] = rows
        return snapshot
