from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

# Employee Schemas
class EmployeeBase(BaseModel):
    employee_name: str
    email: str
    department: Optional[str] = None
    designation: Optional[str] = None
    manager_id: Optional[int] = None
    joining_date: Optional[date] = None
    location: Optional[str] = None
    employment_status: Optional[str] = "Active"

class EmployeeCreate(EmployeeBase):
    pass

class EmployeeResponse(EmployeeBase):
    employee_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Skill Schemas
class SkillBase(BaseModel):
    skill_name: str
    category: Optional[str] = None

class SkillCreate(SkillBase):
    pass

class SkillResponse(SkillBase):
    skill_id: int

    class Config:
        from_attributes = True

# Employee Skill Schemas
class EmployeeSkillBase(BaseModel):
    employee_id: int
    skill_id: int
    proficiency: Optional[str] = None

class EmployeeSkillCreate(EmployeeSkillBase):
    pass

class EmployeeSkillResponse(EmployeeSkillBase):
    id: int

    class Config:
        from_attributes = True

# Project Schemas
class ProjectBase(BaseModel):
    project_name: str
    client_name: Optional[str] = None
    status: Optional[str] = "Active"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    planned_hours: Optional[float] = None
    project_manager_id: Optional[int] = None
    priority: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectResponse(ProjectBase):
    project_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Resource Allocation Schemas
class ResourceAllocationBase(BaseModel):
    employee_id: int
    project_id: int
    allocation_percentage: float = 100.0
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class ResourceAllocationCreate(ResourceAllocationBase):
    pass

class ResourceAllocationResponse(ResourceAllocationBase):
    allocation_id: int

    class Config:
        from_attributes = True

# Timesheet Schemas
class TimesheetBase(BaseModel):
    employee_id: int
    project_id: int
    work_date: date
    hours_logged: float
    submission_status: Optional[str] = "Draft"
    approval_status: Optional[str] = "Pending"

class TimesheetCreate(TimesheetBase):
    pass

class TimesheetResponse(TimesheetBase):
    timesheet_id: int
    created_at: datetime

    class Config:
        from_attributes = True

# Leave Record Schemas
class LeaveRecordBase(BaseModel):
    employee_id: int
    leave_type: str
    start_date: date
    end_date: date
    approval_status: Optional[str] = "Pending"

class LeaveRecordCreate(LeaveRecordBase):
    pass

class LeaveRecordResponse(LeaveRecordBase):
    leave_id: int
    created_at: datetime

    class Config:
        from_attributes = True
