import json
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Callable
from agentworkbench.environment.db import SyntheticEnvironment
from agentworkbench.models.evaluation import ToolCallTrace


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ToolExecutionError(Exception):
    pass


class ToolRegistry:
    """Registry of tools available to agents executing against the synthetic environment."""

    def __init__(self, env: SyntheticEnvironment):
        self.env = env
        self.trace_history: List[ToolCallTrace] = []

    def log_call(self, tool_name: str, arguments: Dict[str, Any], output: Dict[str, Any], error: Optional[str] = None):
        trace = ToolCallTrace(
            step=len(self.trace_history) + 1,
            tool_name=tool_name,
            arguments=arguments,
            output=output,
            error=error,
            timestamp=utc_now_iso()
        )
        self.trace_history.append(trace)

    # ------------------- READ TOOLS -------------------

    def get_employee(self, employee_id: str) -> Dict[str, Any]:
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT * FROM employees WHERE id = ? OR email = ?", (employee_id, employee_id))
            row = cursor.fetchone()
            if not row:
                res = {"error": f"Employee {employee_id} not found."}
                self.log_call("get_employee", {"employee_id": employee_id}, res, error=res["error"])
                return res
            data = dict(row)
            self.log_call("get_employee", {"employee_id": employee_id}, data)
            return data

    def search_employees(self, query: Optional[str] = None, department_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM employees WHERE 1=1"
        params = []
        if query:
            sql += " AND (full_name LIKE ? OR email LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        if department_id:
            sql += " AND department_id = ?"
            params.append(department_id)
        if status:
            sql += " AND status = ?"
            params.append(status)
        
        with self.env.get_cursor() as cursor:
            cursor.execute(sql, params)
            rows = [dict(r) for r in cursor.fetchall()]
            self.log_call("search_employees", {"query": query, "department_id": department_id, "status": status}, {"count": len(rows), "employees": rows})
            return rows

    def get_department(self, department_id: str) -> Dict[str, Any]:
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT * FROM departments WHERE id = ? OR name = ?", (department_id, department_id))
            row = cursor.fetchone()
            if not row:
                res = {"error": f"Department {department_id} not found."}
                self.log_call("get_department", {"department_id": department_id}, res, error=res["error"])
                return res
            data = dict(row)
            self.log_call("get_department", {"department_id": department_id}, data)
            return data

    def get_role(self, role_id: str) -> Dict[str, Any]:
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT * FROM roles WHERE id = ?", (role_id,))
            row = cursor.fetchone()
            if not row:
                res = {"error": f"Role {role_id} not found."}
                self.log_call("get_role", {"role_id": role_id}, res, error=res["error"])
                return res
            data = dict(row)
            data["default_access_groups"] = json.loads(data.pop("default_access_groups_json", "[]"))
            self.log_call("get_role", {"role_id": role_id}, data)
            return data

    def get_user_access(self, employee_id: str) -> List[Dict[str, Any]]:
        with self.env.get_cursor() as cursor:
            cursor.execute(
                """
                SELECT ea.access_group_id, ag.name, ag.description, ea.granted_at, ea.granted_by
                FROM employee_access ea
                JOIN access_groups ag ON ea.access_group_id = ag.id
                WHERE ea.employee_id = ?
                """,
                (employee_id,)
            )
            rows = [dict(r) for r in cursor.fetchall()]
            self.log_call("get_user_access", {"employee_id": employee_id}, {"count": len(rows), "access_groups": rows})
            return rows

    def get_access_group(self, access_group_id: str) -> Dict[str, Any]:
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT * FROM access_groups WHERE id = ?", (access_group_id,))
            row = cursor.fetchone()
            if not row:
                res = {"error": f"Access group {access_group_id} not found."}
                self.log_call("get_access_group", {"access_group_id": access_group_id}, res, error=res["error"])
                return res
            data = dict(row)
            data["allowed_employment_types"] = json.loads(data.pop("allowed_employment_types_json", "[]"))
            self.log_call("get_access_group", {"access_group_id": access_group_id}, data)
            return data

    def get_resource(self, resource_id: str) -> Dict[str, Any]:
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT * FROM resources WHERE id = ? OR name = ?", (resource_id, resource_id))
            row = cursor.fetchone()
            if not row:
                res = {"error": f"Resource {resource_id} not found."}
                self.log_call("get_resource", {"resource_id": resource_id}, res, error=res["error"])
                return res
            data = dict(row)
            self.log_call("get_resource", {"resource_id": resource_id}, data)
            return data

    def search_resources(self, query: str) -> List[Dict[str, Any]]:
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT * FROM resources WHERE name LIKE ? OR resource_type LIKE ?", (f"%{query}%", f"%{query}%"))
            rows = [dict(r) for r in cursor.fetchall()]
            self.log_call("search_resources", {"query": query}, {"count": len(rows), "resources": rows})
            return rows

    def get_device(self, device_id: str) -> Dict[str, Any]:
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT * FROM devices WHERE id = ? OR serial_number = ?", (device_id, device_id))
            row = cursor.fetchone()
            if not row:
                res = {"error": f"Device {device_id} not found."}
                self.log_call("get_device", {"device_id": device_id}, res, error=res["error"])
                return res
            data = dict(row)
            self.log_call("get_device", {"device_id": device_id}, data)
            return data

    def search_devices(self, assigned_to_employee_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM devices WHERE 1=1"
        params = []
        if assigned_to_employee_id:
            sql += " AND assigned_to_employee_id = ?"
            params.append(assigned_to_employee_id)
        if status:
            sql += " AND status = ?"
            params.append(status)
        with self.env.get_cursor() as cursor:
            cursor.execute(sql, params)
            rows = [dict(r) for r in cursor.fetchall()]
            self.log_call("search_devices", {"assigned_to_employee_id": assigned_to_employee_id, "status": status}, {"count": len(rows), "devices": rows})
            return rows

    def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
            t_row = cursor.fetchone()
            if not t_row:
                res = {"error": f"Ticket {ticket_id} not found."}
                self.log_call("get_ticket", {"ticket_id": ticket_id}, res, error=res["error"])
                return res
            ticket_data = dict(t_row)
            ticket_data["tags"] = json.loads(ticket_data.pop("tags_json", "[]"))
            
            cursor.execute("SELECT * FROM ticket_comments WHERE ticket_id = ? ORDER BY created_at ASC", (ticket_id,))
            comments = [dict(r) for r in cursor.fetchall()]
            ticket_data["comments"] = comments
            self.log_call("get_ticket", {"ticket_id": ticket_id}, ticket_data)
            return ticket_data

    def search_tickets(self, requester_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM tickets WHERE 1=1"
        params = []
        if requester_id:
            sql += " AND requester_employee_id = ?"
            params.append(requester_id)
        if status:
            sql += " AND status = ?"
            params.append(status)
        with self.env.get_cursor() as cursor:
            cursor.execute(sql, params)
            rows = []
            for r in cursor.fetchall():
                d = dict(r)
                d["tags"] = json.loads(d.pop("tags_json", "[]"))
                rows.append(d)
            self.log_call("search_tickets", {"requester_id": requester_id, "status": status}, {"count": len(rows), "tickets": rows})
            return rows

    def get_policy(self, policy_id: str) -> Dict[str, Any]:
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT * FROM policies WHERE id = ?", (policy_id,))
            row = cursor.fetchone()
            if not row:
                res = {"error": f"Policy {policy_id} not found."}
                self.log_call("get_policy", {"policy_id": policy_id}, res, error=res["error"])
                return res
            data = dict(row)
            self.log_call("get_policy", {"policy_id": policy_id}, data)
            return data

    def search_policies(self, query: str) -> List[Dict[str, Any]]:
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT * FROM policies WHERE title LIKE ? OR content LIKE ? OR category LIKE ?", (f"%{query}%", f"%{query}%", f"%{query}%"))
            rows = [dict(r) for r in cursor.fetchall()]
            self.log_call("search_policies", {"query": query}, {"count": len(rows), "policies": rows})
            return rows

    # ------------------- ACTION / MUTATION TOOLS -------------------

    def grant_access(self, employee_id: str, access_group_id: str) -> Dict[str, Any]:
        with self.env.get_cursor() as cursor:
            cursor.execute("SELECT id FROM employees WHERE id = ?", (employee_id,))
            if not cursor.fetchone():
                res = {"success": False, "error": f"Employee {employee_id} does not exist."}
                self.log_call("grant_access", {"employee_id": employee_id, "access_group_id": access_group_id}, res, error=res["error"])
                return res

            cursor.execute("SELECT id FROM access_groups WHERE id = ?", (access_group_id,))
            if not cursor.fetchone():
                res = {"success": False, "error": f"Access group {access_group_id} does not exist."}
                self.log_call("grant_access", {"employee_id": employee_id, "access_group_id": access_group_id}, res, error=res["error"])
                return res

            now = utc_now_iso()
            cursor.execute(
                "INSERT OR IGNORE INTO employee_access (employee_id, access_group_id, granted_at, granted_by) VALUES (?, ?, ?, ?)",
                (employee_id, access_group_id, now, "agent")
            )
            res = {"success": True, "message": f"Granted access group '{access_group_id}' to employee '{employee_id}'."}
            self.log_call("grant_access", {"employee_id": employee_id, "access_group_id": access_group_id}, res)
            return res

    def revoke_access(self, employee_id: str, access_group_id: str) -> Dict[str, Any]:
        with self.env.get_cursor() as cursor:
            cursor.execute(
                "DELETE FROM employee_access WHERE employee_id = ? AND access_group_id = ?",
                (employee_id, access_group_id)
            )
            res = {"success": True, "message": f"Revoked access group '{access_group_id}' from employee '{employee_id}'."}
            self.log_call("revoke_access", {"employee_id": employee_id, "access_group_id": access_group_id}, res)
            return res

    def disable_account(self, employee_id: str, status: str = "terminated") -> Dict[str, Any]:
        if status not in ["terminated", "suspended"]:
            status = "terminated"
        with self.env.get_cursor() as cursor:
            cursor.execute("UPDATE employees SET status = ? WHERE id = ?", (status, employee_id))
            res = {"success": True, "message": f"Employee '{employee_id}' status set to '{status}'."}
            self.log_call("disable_account", {"employee_id": employee_id, "status": status}, res)
            return res

    def enable_account(self, employee_id: str) -> Dict[str, Any]:
        with self.env.get_cursor() as cursor:
            cursor.execute("UPDATE employees SET status = 'active' WHERE id = ?", (employee_id,))
            res = {"success": True, "message": f"Employee '{employee_id}' status set to 'active'."}
            self.log_call("enable_account", {"employee_id": employee_id}, res)
            return res

    def update_employee_department(self, employee_id: str, department_id: str, role_id: Optional[str] = None) -> Dict[str, Any]:
        with self.env.get_cursor() as cursor:
            if role_id:
                cursor.execute("UPDATE employees SET department_id = ?, role_id = ? WHERE id = ?", (department_id, role_id, employee_id))
            else:
                cursor.execute("UPDATE employees SET department_id = ? WHERE id = ?", (department_id, employee_id))
            res = {"success": True, "message": f"Updated employee '{employee_id}' department to '{department_id}'."}
            self.log_call("update_employee_department", {"employee_id": employee_id, "department_id": department_id, "role_id": role_id}, res)
            return res

    def assign_device(self, device_id: str, employee_id: Optional[str]) -> Dict[str, Any]:
        new_status = "assigned" if employee_id else "in_stock"
        with self.env.get_cursor() as cursor:
            cursor.execute(
                "UPDATE devices SET assigned_to_employee_id = ?, status = ? WHERE id = ?",
                (employee_id, new_status, device_id)
            )
            res = {"success": True, "message": f"Assigned device '{device_id}' to employee '{employee_id}' (status: {new_status})."}
            self.log_call("assign_device", {"device_id": device_id, "employee_id": employee_id}, res)
            return res

    def update_device_status(self, device_id: str, status: str) -> Dict[str, Any]:
        with self.env.get_cursor() as cursor:
            if status in ["in_stock", "lost", "stolen", "decommissioned", "repair"]:
                cursor.execute("UPDATE devices SET status = ? WHERE id = ?", (status, device_id))
            else:
                cursor.execute("UPDATE devices SET status = ? WHERE id = ?", (status, device_id))
            res = {"success": True, "message": f"Device '{device_id}' status updated to '{status}'."}
            self.log_call("update_device_status", {"device_id": device_id, "status": status}, res)
            return res

    def add_ticket_comment(self, ticket_id: str, content: str, author: str = "Agent") -> Dict[str, Any]:
        comment_id = f"cmt-{uuid.uuid4().hex[:8]}"
        now = utc_now_iso()
        with self.env.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO ticket_comments (id, ticket_id, author, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (comment_id, ticket_id, author, content, now)
            )
            cursor.execute("UPDATE tickets SET updated_at = ? WHERE id = ?", (now, ticket_id))
            res = {"success": True, "comment_id": comment_id, "message": "Comment added to ticket."}
            self.log_call("add_ticket_comment", {"ticket_id": ticket_id, "content": content, "author": author}, res)
            return res

    def update_ticket(self, ticket_id: str, status: Optional[str] = None, assigned_to: Optional[str] = None, priority: Optional[str] = None) -> Dict[str, Any]:
        sql = "UPDATE tickets SET updated_at = ?"
        params = [utc_now_iso()]
        if status:
            sql += ", status = ?"
            params.append(status)
        if assigned_to:
            sql += ", assigned_to = ?"
            params.append(assigned_to)
        if priority:
            sql += ", priority = ?"
            params.append(priority)
        sql += " WHERE id = ?"
        params.append(ticket_id)

        with self.env.get_cursor() as cursor:
            cursor.execute(sql, params)
            res = {"success": True, "message": f"Ticket '{ticket_id}' updated."}
            self.log_call("update_ticket", {"ticket_id": ticket_id, "status": status, "assigned_to": assigned_to, "priority": priority}, res)
            return res

    def resolve_ticket(self, ticket_id: str, resolution_summary: str) -> Dict[str, Any]:
        self.add_ticket_comment(ticket_id, f"RESOLUTION: {resolution_summary}", author="Agent")
        with self.env.get_cursor() as cursor:
            cursor.execute(
                "UPDATE tickets SET status = 'resolved', updated_at = ? WHERE id = ?",
                (utc_now_iso(), ticket_id)
            )
            res = {"success": True, "message": f"Ticket '{ticket_id}' resolved."}
            self.log_call("resolve_ticket", {"ticket_id": ticket_id, "resolution_summary": resolution_summary}, res)
            return res

    def escalate_ticket(self, ticket_id: str, reason: str) -> Dict[str, Any]:
        self.add_ticket_comment(ticket_id, f"ESCALATION REASON: {reason}", author="Agent")
        with self.env.get_cursor() as cursor:
            cursor.execute(
                "UPDATE tickets SET status = 'escalated', updated_at = ? WHERE id = ?",
                (utc_now_iso(), ticket_id)
            )
            res = {"success": True, "message": f"Ticket '{ticket_id}' escalated."}
            self.log_call("escalate_ticket", {"ticket_id": ticket_id, "reason": reason}, res)
            return res

    def finish(self, reason: str = "Task completed.") -> Dict[str, Any]:
        """Tool called by LLM to signal task completion."""
        res = {"success": True, "message": f"Agent finished task: {reason}"}
        self.log_call("finish", {"reason": reason}, res)
        return res

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Returns OpenAI-compatible tool schema definitions for LLMs."""
        return [
            {"name": "get_employee", "description": "Fetch details of an employee by ID or email.", "parameters": {"type": "object", "properties": {"employee_id": {"type": "string"}}, "required": ["employee_id"]}},
            {"name": "search_employees", "description": "Search employees by name, department, or status.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "department_id": {"type": "string"}, "status": {"type": "string"}}}},
            {"name": "get_department", "description": "Fetch department info.", "parameters": {"type": "object", "properties": {"department_id": {"type": "string"}}, "required": ["department_id"]}},
            {"name": "get_role", "description": "Fetch role details including default access groups.", "parameters": {"type": "object", "properties": {"role_id": {"type": "string"}}, "required": ["role_id"]}},
            {"name": "get_user_access", "description": "Get all access groups granted to an employee.", "parameters": {"type": "object", "properties": {"employee_id": {"type": "string"}}, "required": ["employee_id"]}},
            {"name": "get_access_group", "description": "Fetch access group details.", "parameters": {"type": "object", "properties": {"access_group_id": {"type": "string"}}, "required": ["access_group_id"]}},
            {"name": "get_resource", "description": "Fetch resource details.", "parameters": {"type": "object", "properties": {"resource_id": {"type": "string"}}, "required": ["resource_id"]}},
            {"name": "search_resources", "description": "Search resources by name or type.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
            {"name": "get_device", "description": "Fetch device details by ID or serial number.", "parameters": {"type": "object", "properties": {"device_id": {"type": "string"}}, "required": ["device_id"]}},
            {"name": "search_devices", "description": "Search devices by employee or status.", "parameters": {"type": "object", "properties": {"assigned_to_employee_id": {"type": "string"}, "status": {"type": "string"}}}},
            {"name": "get_ticket", "description": "Get ticket details and comments.", "parameters": {"type": "object", "properties": {"ticket_id": {"type": "string"}}, "required": ["ticket_id"]}},
            {"name": "search_tickets", "description": "Search tickets by requester or status.", "parameters": {"type": "object", "properties": {"requester_id": {"type": "string"}, "status": {"type": "string"}}}},
            {"name": "get_policy", "description": "Fetch corporate policy text.", "parameters": {"type": "object", "properties": {"policy_id": {"type": "string"}}, "required": ["policy_id"]}},
            {"name": "search_policies", "description": "Search security & IT policies.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}},
            {"name": "grant_access", "description": "Grant an access group to an employee.", "parameters": {"type": "object", "properties": {"employee_id": {"type": "string"}, "access_group_id": {"type": "string"}}, "required": ["employee_id", "access_group_id"]}},
            {"name": "revoke_access", "description": "Revoke an access group from an employee.", "parameters": {"type": "object", "properties": {"employee_id": {"type": "string"}, "access_group_id": {"type": "string"}}, "required": ["employee_id", "access_group_id"]}},
            {"name": "disable_account", "description": "Set employee status to terminated or suspended.", "parameters": {"type": "object", "properties": {"employee_id": {"type": "string"}, "status": {"type": "string"}}, "required": ["employee_id"]}},
            {"name": "enable_account", "description": "Set employee status to active.", "parameters": {"type": "object", "properties": {"employee_id": {"type": "string"}}, "required": ["employee_id"]}},
            {"name": "update_employee_department", "description": "Update employee's department and role.", "parameters": {"type": "object", "properties": {"employee_id": {"type": "string"}, "department_id": {"type": "string"}, "role_id": {"type": "string"}}, "required": ["employee_id", "department_id"]}},
            {"name": "assign_device", "description": "Assign or unassign a hardware device to an employee.", "parameters": {"type": "object", "properties": {"device_id": {"type": "string"}, "employee_id": {"type": "string"}}, "required": ["device_id"]}},
            {"name": "update_device_status", "description": "Update device state (assigned, in_stock, lost, stolen, decommissioned).", "parameters": {"type": "object", "properties": {"device_id": {"type": "string"}, "status": {"type": "string"}}, "required": ["device_id", "status"]}},
            {"name": "add_ticket_comment", "description": "Add a comment to an open ticket.", "parameters": {"type": "object", "properties": {"ticket_id": {"type": "string"}, "content": {"type": "string"}}, "required": ["ticket_id", "content"]}},
            {"name": "update_ticket", "description": "Update ticket status or assignment.", "parameters": {"type": "object", "properties": {"ticket_id": {"type": "string"}, "status": {"type": "string"}, "assigned_to": {"type": "string"}, "priority": {"type": "string"}}, "required": ["ticket_id"]}},
            {"name": "resolve_ticket", "description": "Mark ticket resolved with summary comment.", "parameters": {"type": "object", "properties": {"ticket_id": {"type": "string"}, "resolution_summary": {"type": "string"}}, "required": ["ticket_id", "resolution_summary"]}},
            {"name": "escalate_ticket", "description": "Escalate ticket with reason.", "parameters": {"type": "object", "properties": {"ticket_id": {"type": "string"}, "reason": {"type": "string"}}, "required": ["ticket_id", "reason"]}},
            {"name": "finish", "description": "Signal task completion when work is verified.", "parameters": {"type": "object", "properties": {"reason": {"type": "string"}}, "required": ["reason"]}}
        ]

    def execute_tool(self, tool_name: str, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        if not hasattr(self, tool_name):
            err = f"Unknown tool: {tool_name}"
            self.log_call(tool_name, kwargs, {"error": err}, error=err)
            return {"error": err}
        method: Callable = getattr(self, tool_name)
        try:
            return method(**kwargs)
        except Exception as e:
            err = f"Execution error in {tool_name}: {str(e)}"
            self.log_call(tool_name, kwargs, {"error": err}, error=err)
            return {"error": err}
