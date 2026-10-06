from datetime import datetime, timezone
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"
    ONBOARDING = "onboarding"


class DeviceStatus(str, Enum):
    ASSIGNED = "assigned"
    IN_STOCK = "in_stock"
    LOST = "lost"
    STOLEN = "stolen"
    DECOMMISSIONED = "decommissioned"
    REPAIR = "repair"


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Employee(BaseModel):
    id: str
    email: str
    full_name: str
    department_id: str
    role_id: str
    employment_type: str = "full_time"  # full_time, contractor, intern
    status: EmployeeStatus = EmployeeStatus.ACTIVE
    manager_id: Optional[str] = None
    created_at: str = Field(default_factory=utc_now_iso)


class Department(BaseModel):
    id: str
    name: str
    head_employee_id: Optional[str] = None


class Role(BaseModel):
    id: str
    title: str
    department_id: str
    default_access_groups: List[str] = Field(default_factory=list)


class AccessGroup(BaseModel):
    id: str
    name: str
    description: str
    requires_approval: bool = False
    allowed_employment_types: List[str] = Field(default_factory=lambda: ["full_time", "contractor", "intern"])


class Resource(BaseModel):
    id: str
    name: str
    resource_type: str  # software, database, server, repo
    sensitivity_level: str = "medium"  # low, medium, high, critical
    access_group_id: str


class Device(BaseModel):
    id: str
    serial_number: str
    model: str
    device_type: str  # laptop, desktop, mobile
    assigned_to_employee_id: Optional[str] = None
    status: DeviceStatus = DeviceStatus.IN_STOCK


class TicketComment(BaseModel):
    id: str
    ticket_id: str
    author: str
    content: str
    created_at: str = Field(default_factory=utc_now_iso)


class Ticket(BaseModel):
    id: str
    title: str
    description: str
    requester_employee_id: str
    target_employee_id: Optional[str] = None
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM
    assigned_to: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    comments: List[TicketComment] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class Policy(BaseModel):
    id: str
    title: str
    content: str
    category: str


class EmployeeAccess(BaseModel):
    employee_id: str
    access_group_id: str
    granted_at: str = Field(default_factory=utc_now_iso)
    granted_by: str = "system"
