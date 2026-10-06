from typing import Dict, List, Any, Tuple


class StateDiffEngine:
    """Computes exact, structured state differences between initial and final environment snapshots."""

    @staticmethod
    def compute_diff(
        initial_snapshot: Dict[str, List[Dict[str, Any]]],
        final_snapshot: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:

        diff = {
            "employee_changes": [],
            "access_changes": [],
            "device_changes": [],
            "ticket_changes": [],
            "comment_changes": []
        }

        # 1. Employees diff
        init_emps = {e["id"]: e for e in initial_snapshot.get("employees", [])}
        final_emps = {e["id"]: e for e in final_snapshot.get("employees", [])}
        for emp_id, final_data in final_emps.items():
            init_data = init_emps.get(emp_id)
            if not init_data:
                diff["employee_changes"].append({"employee_id": emp_id, "action": "created", "after": final_data})
            elif init_data != final_data:
                diff["employee_changes"].append({
                    "employee_id": emp_id,
                    "action": "modified",
                    "before": {k: v for k, v in init_data.items() if init_data[k] != final_data[k]},
                    "after": {k: v for k, v in final_data.items() if init_data[k] != final_data[k]}
                })

        # 2. Access groups diff (employee_access)
        init_access = {(a["employee_id"], a["access_group_id"]) for a in initial_snapshot.get("employee_access", [])}
        final_access = {(a["employee_id"], a["access_group_id"]) for a in final_snapshot.get("employee_access", [])}

        for emp_id, group_id in final_access - init_access:
            diff["access_changes"].append({"employee_id": emp_id, "access_group_id": group_id, "action": "granted"})
        for emp_id, group_id in init_access - final_access:
            diff["access_changes"].append({"employee_id": emp_id, "access_group_id": group_id, "action": "revoked"})

        # 3. Devices diff
        init_devs = {d["id"]: d for d in initial_snapshot.get("devices", [])}
        final_devs = {d["id"]: d for d in final_snapshot.get("devices", [])}
        for dev_id, final_data in final_devs.items():
            init_data = init_devs.get(dev_id)
            if init_data and init_data != final_data:
                diff["device_changes"].append({
                    "device_id": dev_id,
                    "action": "modified",
                    "before": {k: v for k, v in init_data.items() if init_data[k] != final_data[k]},
                    "after": {k: v for k, v in final_data.items() if init_data[k] != final_data[k]}
                })

        # 4. Tickets diff
        init_tickets = {t["id"]: t for t in initial_snapshot.get("tickets", [])}
        final_tickets = {t["id"]: t for t in final_snapshot.get("tickets", [])}
        for tck_id, final_data in final_tickets.items():
            init_data = init_tickets.get(tck_id)
            if init_data and init_data != final_data:
                diff["ticket_changes"].append({
                    "ticket_id": tck_id,
                    "action": "modified",
                    "before": {k: v for k, v in init_data.items() if init_data.get(k) != final_data.get(k) and k != "updated_at"},
                    "after": {k: v for k, v in final_data.items() if init_data.get(k) != final_data.get(k) and k != "updated_at"}
                })

        # 5. Ticket comments diff
        init_cmts = {c["id"] for c in initial_snapshot.get("ticket_comments", [])}
        for cmt in final_snapshot.get("ticket_comments", []):
            if cmt["id"] not in init_cmts:
                diff["comment_changes"].append({
                    "comment_id": cmt["id"],
                    "ticket_id": cmt["ticket_id"],
                    "author": cmt["author"],
                    "content": cmt["content"]
                })

        return diff
