import datetime
import random
from sqlalchemy.future import select
from src.core.database import SessionLocal
from models.employee import Employee, Skill, EmployeeSkill
from models.project import Project, ResourceAllocation
from models.timesheet import Timesheet, LeaveRecord
from models.department import Department
from models.role import Role
from models.leave_balance import LeaveBalance
from models.leave_request import LeaveRequest
from models.attendance import Attendance
from models.payroll import Payroll
from models.job_opening import JobOpening
from models.candidate import Candidate
from models.ticket import Ticket
from models.policy_document import PolicyDocument

# ── Indian names ──────────────────────────────────────────────────────────────
FIRST_NAMES = [
    "Rahul", "Priya", "Amit", "Neha", "Vikram", "Sneha", "Rohit", "Anjali",
    "Suresh", "Kavita", "Ravi", "Divya", "Sanjay", "Pooja", "Arjun", "Kiran",
    "Manish", "Aarti", "Nitin", "Swati", "Deepak", "Ritu", "Ajay", "Shikha",
    "Vivek", "Megha", "Alok", "Nidhi", "Gaurav", "Preeti", "Yash", "Shreya",
    "Kunal", "Ananya", "Rohan", "Isha", "Varun", "Tanya", "Siddharth", "Aisha"
]

LAST_NAMES = [
    "Sharma", "Patel", "Singh", "Gupta", "Kumar", "Reddy", "Rao", "Das",
    "Verma", "Chauhan", "Jain", "Bose", "Menon", "Nair", "Iyer", "Pillai",
    "Yadav", "Mishra", "Joshi", "Desai", "Ahuja", "Kapoor", "Malhotra", "Saxena"
]

DEPARTMENTS = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Product", "Design", "QA", "DevOps"]
ROLES       = ["Junior", "Mid-Level", "Senior", "Lead", "Manager", "Director"]

SKILLS_LIST = [
    "Python", "React", "Node.js", "Java", "Go", "TypeScript", "AWS", "Azure",
    "GCP", "SQL", "MongoDB", "Figma", "Kubernetes", "Docker", "Terraform",
    "Salesforce", "SEO", "Content Writing", "Digital Marketing", "Recruitment",
    "Financial Modeling", "Agile", "Scrum", "ML/AI", "FastAPI"
]

PROJECT_NAMES = [
    "Yottaflex AI Migration", "Enterprise Dashboard V2", "Cloud Infrastructure Optimization",
    "Q3 Marketing Campaign", "Sales CRM Overhaul", "Employee Portal Upgrade",
    "Financial Audit Automation", "Mobile App Replatforming", "Data Warehouse Redesign",
    "Customer Success Portal", "DevOps Pipeline Modernization", "AI Copilot Integration",
    "Security Compliance Framework", "API Gateway Upgrade", "Analytics Platform V3"
]

ACTIVITY_TYPES = [
    "Development", "Code Review", "Testing / QA", "Design", "Meeting",
    "Documentation", "Research", "DevOps / Deployment", "Support", "Training"
]

LEAVE_TYPES = ["Sick", "Vacation", "Personal", "Casual", "Compensatory"]


async def seed_data():
    async with SessionLocal() as db:
        print("Checking and seeding Yottaflex Workforce Data...")

        exist_emp = await db.execute(select(Employee))
        employees = list(exist_emp.scalars().all())
        has_employees = len(employees) > 0

        # Load managers
        managers = []
        if has_employees:
            managers = employees[:10]
        else:
            # ── 1. Skills ────────────────────────────────────────────────────────
            db_skills: list[Skill] = []
            for s_name in SKILLS_LIST:
                skill = Skill(skill_name=s_name, category="Technical")
                db.add(skill)
                db_skills.append(skill)
            await db.flush()

            # ── 2. Employees (60 employees) ──────────────────────────────────────
            used_emails: set[str] = set()
            for i in range(60):
                fname = random.choice(FIRST_NAMES)
                lname = random.choice(LAST_NAMES)
                dept  = random.choice(DEPARTMENTS)

                role_base = random.choice(ROLES)
                if dept == "Engineering":
                    designation = f"{role_base} Software Engineer"
                elif dept == "Design":
                    designation = f"{role_base} Product Designer"
                elif dept == "QA":
                    designation = f"{role_base} QA Engineer"
                elif dept == "DevOps":
                    designation = f"{role_base} DevOps Engineer"
                else:
                    designation = f"{role_base} {dept} Specialist"

                # Unique e-mail
                base_email = f"{fname.lower()}.{lname.lower()}"
                email = f"{base_email}{i}@yottaflex.com"
                while email in used_emails:
                    email = f"{base_email}{i}_{random.randint(10,99)}@yottaflex.com"
                used_emails.add(email)

                emp = Employee(
                    employee_name=f"{fname} {lname}",
                    email=email,
                    department=dept,
                    designation=designation,
                    joining_date=datetime.date.today() - datetime.timedelta(days=random.randint(60, 2500)),
                    location=random.choice(["Bangalore", "Mumbai", "Hyderabad", "Pune", "Chennai", "Delhi"]),
                    employment_status="Active"
                )
                db.add(emp)
                employees.append(emp)
            await db.flush()

            # ── 3. Managers (first 10 employees become managers) ─────────────────
            managers = employees[:10]
            for emp in employees[10:]:
                emp.manager_id = random.choice(managers).employee_id
            await db.flush()

            # ── 4. Employee Skills ────────────────────────────────────────────────
            for emp in employees:
                num_skills = random.randint(2, 6)
                selected = random.sample(db_skills, min(num_skills, len(db_skills)))
                for skill in selected:
                    db.add(EmployeeSkill(
                        employee_id=emp.employee_id,
                        skill_id=skill.skill_id,
                        proficiency=random.choice(["Beginner", "Intermediate", "Expert"])
                    ))
            await db.flush()

            # ── 5. Projects ───────────────────────────────────────────────────────
            projects: list[Project] = []
            today = datetime.date.today()
            for p_name in PROJECT_NAMES:
                status     = random.choices(["Planned", "Active", "At Risk", "Completed"], weights=[5, 60, 25, 10])[0]
                start_date = today - datetime.timedelta(days=random.randint(10, 180))
                end_date   = start_date + datetime.timedelta(days=random.randint(60, 400))
                proj = Project(
                    project_name=p_name,
                    client_name=random.choice(["Accenture", "Infosys", "Wipro", "TCS", "HCL", "Internal"]),
                    status=status,
                    start_date=start_date,
                    end_date=end_date,
                    budget=float(random.randint(500_000, 15_000_000)),
                    planned_hours=float(random.randint(1000, 8000)),
                    priority=random.choice(["High", "Medium", "Low"])
                )
                db.add(proj)
                projects.append(proj)
            await db.flush()

            # ── 6. Resource Allocation ────────────────────────────────────────────
            active_projects = [p for p in projects if p.status in ("Active", "At Risk")]
            proj_emp_map: dict[int, list[int]] = {}  # project_id -> [employee_ids]
            for proj in active_projects:
                team_size = random.randint(4, 10)
                team      = random.sample(employees, team_size)
                proj_emp_map[proj.project_id] = [emp.employee_id for emp in team]
                for emp in team:
                    db.add(ResourceAllocation(
                        employee_id=emp.employee_id,
                        project_id=proj.project_id,
                        allocation_percentage=float(random.choice([20.0, 50.0, 80.0, 100.0])),
                        start_date=proj.start_date,
                        end_date=proj.end_date
                    ))
            await db.flush()

            # Build reverse map: employee_id -> [project_ids]
            emp_proj_map: dict[int, list[int]] = {}
            for proj_id, emp_ids in proj_emp_map.items():
                for eid in emp_ids:
                    emp_proj_map.setdefault(eid, []).append(proj_id)

            # ── 7. Timesheet Entries (last 90 days, dense data) ──────────────────
            fallback_proj_id = active_projects[0].project_id if active_projects else 1
            for emp in employees:
                emp_proj_ids = emp_proj_map.get(emp.employee_id, [fallback_proj_id])
                if not emp_proj_ids:
                    emp_proj_ids = [fallback_proj_id]

                for day_offset in range(90):
                    work_date = today - datetime.timedelta(days=day_offset)
                    if work_date.weekday() >= 5:       # skip weekends
                        continue
                    if random.random() < 0.12:         # ~12 % absence rate
                        continue

                    sessions = random.randint(1, 3)
                    remaining_hours = random.uniform(6.0, 9.0)
                    for _ in range(sessions):
                        hours = round(random.uniform(1.0, min(remaining_hours, 4.5)), 1)
                        remaining_hours -= hours
                        if remaining_hours < 0.5:
                            break

                        approval = random.choices(
                            ["Approved", "Pending", "Rejected"],
                            weights=[70, 25, 5]
                        )[0]

                        db.add(Timesheet(
                            employee_id=emp.employee_id,
                            project_id=random.choice(emp_proj_ids),
                            work_date=work_date,
                            hours_logged=hours,
                            activity_type=random.choice(ACTIVITY_TYPES),
                            note=random.choice([
                                "Implemented feature X and wrote unit tests.",
                                "Participated in sprint planning meeting.",
                                "Fixed critical bug in production pipeline.",
                                "Conducted code review for PR #142.",
                                "Deployed hotfix to staging environment.",
                                "Collaborated with design team on UI specs.",
                                "Resolved client escalation ticket.",
                                "Reviewed system architecture proposal.",
                                "Database query optimization work.",
                                "Prepared weekly status report.",
                                None
                            ]),
                            submission_status="Submitted",
                            approval_status=approval
                        ))

            await db.flush()

            # ── 8. Leave Records ──────────────────────────────────────────────────
            for emp in employees:
                for _ in range(random.randint(1, 4)):
                    leave_start = today - datetime.timedelta(days=random.randint(1, 180))
                    leave_end   = leave_start + datetime.timedelta(days=random.randint(0, 5))
                    db.add(LeaveRecord(
                        employee_id=emp.employee_id,
                        leave_type=random.choice(LEAVE_TYPES),
                        start_date=leave_start,
                        end_date=min(leave_end, today),
                        approval_status=random.choices(["Approved", "Rejected", "Pending"], weights=[65, 15, 20])[0]
                    ))

                if random.random() < 0.25:
                    future_start = today + datetime.timedelta(days=random.randint(1, 30))
                    future_end   = future_start + datetime.timedelta(days=random.randint(0, 4))
                    db.add(LeaveRecord(
                        employee_id=emp.employee_id,
                        leave_type=random.choice(LEAVE_TYPES),
                        start_date=future_start,
                        end_date=future_end,
                        approval_status="Pending"
                    ))
            await db.flush()

        # Seed new tables
        today = datetime.date.today()

        # 1. Departments
        exist_dept = await db.execute(select(Department))
        if exist_dept.scalars().first() is None:
            for idx, dept_name in enumerate(DEPARTMENTS):
                mgr = managers[idx % len(managers)] if managers else None
                db.add(Department(
                    department_name=dept_name,
                    manager_id=mgr.employee_id if mgr else None,
                    budget=float(random.randint(1_000_000, 10_000_000))
                ))
            await db.flush()

        # 2. Roles
        exist_role = await db.execute(select(Role))
        if exist_role.scalars().first() is None:
            dept_stmt = await db.execute(select(Department))
            all_depts = dept_stmt.scalars().all()
            dept_map = {d.department_name: d.department_id for d in all_depts}
            
            role_names = [
                ("Software Engineer", "Engineering", 80000.0),
                ("Product Designer", "Design", 75000.0),
                ("QA Engineer", "QA", 65000.0),
                ("DevOps Engineer", "DevOps", 85000.0),
                ("HR Specialist", "HR", 60000.0),
                ("Finance Analyst", "Finance", 70000.0),
                ("Marketing Specialist", "Marketing", 62000.0),
                ("Sales Representative", "Sales", 55000.0),
                ("Product Manager", "Product", 95000.0)
            ]
            for r_name, dept_name, base_sal in role_names:
                db.add(Role(
                    role_name=r_name,
                    department_id=dept_map.get(dept_name),
                    base_salary=base_sal
                ))
            await db.flush()

        # 3. Leave Balance
        exist_lb = await db.execute(select(LeaveBalance))
        if exist_lb.scalars().first() is None:
            for emp in employees:
                annual_allowances = {"Sick": 12, "Vacation": 15, "Personal": 6, "Casual": 10, "Compensatory": 5}
                for lt, allowance in annual_allowances.items():
                    used = random.randint(0, 5)
                    pending = random.randint(0, 2)
                    db.add(LeaveBalance(
                        employee_id=emp.employee_id,
                        leave_type=lt,
                        allocated=allowance,
                        used=used,
                        pending=pending
                    ))
            await db.flush()

        # 4. Leave Requests
        exist_lr = await db.execute(select(LeaveRequest))
        if exist_lr.scalars().first() is None:
            lr_stmt = await db.execute(select(LeaveRecord))
            leave_records = lr_stmt.scalars().all()
            for record in leave_records:
                db.add(LeaveRequest(
                    employee_id=record.employee_id,
                    leave_type=record.leave_type,
                    start_date=record.start_date,
                    end_date=record.end_date,
                    reason="Personal reasons / Sick leave" if record.leave_type == "Sick" else "Vacation planning",
                    approval_status=record.approval_status,
                    created_at=datetime.datetime.combine(record.start_date, datetime.time(9, 0))
                ))
            await db.flush()

        # 5. Attendance
        exist_att = await db.execute(select(Attendance))
        if exist_att.scalars().first() is None:
            for emp in employees:
                for day_offset in range(30):
                    work_date = today - datetime.timedelta(days=day_offset)
                    if work_date.weekday() >= 5:
                        continue
                    rand = random.random()
                    if rand < 0.90:
                        status = "Present"
                        check_in_hour = 8 if random.random() < 0.3 else 9
                        check_in_min = random.randint(30, 59) if check_in_hour == 8 else random.randint(0, 30)
                        check_out_hour = 17 if random.random() < 0.3 else 18
                        check_out_min = random.randint(30, 59) if check_out_hour == 17 else random.randint(0, 30)
                        check_in = datetime.datetime.combine(work_date, datetime.time(check_in_hour, check_in_min))
                        check_out = datetime.datetime.combine(work_date, datetime.time(check_out_hour, check_out_min))
                    elif rand < 0.95:
                        status = "Leave"
                        check_in = None
                        check_out = None
                    else:
                        status = "Absent"
                        check_in = None
                        check_out = None
                    
                    db.add(Attendance(
                        employee_id=emp.employee_id,
                        work_date=work_date,
                        check_in=check_in,
                        check_out=check_out,
                        status=status
                    ))
            await db.flush()

        # 6. Payroll
        exist_pay = await db.execute(select(Payroll))
        if exist_pay.scalars().first() is None:
            for emp in employees:
                base = 60000.0
                if "Senior" in (emp.designation or ""):
                    base = 90000.0
                elif "Lead" in (emp.designation or ""):
                    base = 110000.0
                elif "Manager" in (emp.designation or ""):
                    base = 130000.0
                elif "Director" in (emp.designation or ""):
                    base = 180000.0
                    
                for m_offset in range(3):
                    pay_date = today.replace(day=28) - datetime.timedelta(days=m_offset * 30)
                    month = pay_date.month
                    year = pay_date.year
                    allowance = round(random.uniform(2000.0, 5000.0), 2)
                    deductions = round(random.uniform(1000.0, 3000.0), 2)
                    net = base + allowance - deductions
                    
                    db.add(Payroll(
                        employee_id=emp.employee_id,
                        month=month,
                        year=year,
                        basic_salary=base,
                        allowances=allowance,
                        deductions=deductions,
                        net_salary=net,
                        payment_status="Paid",
                        payment_date=datetime.datetime.combine(pay_date, datetime.time(10, 0))
                    ))
            await db.flush()

        # 7. Job Openings
        exist_jobs = await db.execute(select(JobOpening))
        if exist_jobs.scalars().first() is None:
            jobs = [
                ("Senior React Developer", "Engineering", "We are looking for a Senior React Developer to join our team to build next-gen portals.", "5+ years experience, React, TypeScript, Redux"),
                ("HR Manager", "HR", "Oversee human resources department operations and employee relations.", "7+ years experience, HR Management, Communication"),
                ("DevOps Engineer", "DevOps", "Manage and automate cloud infrastructure deployment pipelines.", "3+ years experience, AWS, Kubernetes, Terraform"),
                ("Product Designer", "Design", "Create stunning user experiences and UI mockups.", "3+ years experience, Figma, Portfolio required"),
                ("Finance Lead", "Finance", "Manage financial modeling, planning, and audits.", "5+ years experience, CPA/MBA, Excel")
            ]
            for title, dept, desc, reqs in jobs:
                db.add(JobOpening(
                    title=title,
                    department=dept,
                    description=desc,
                    requirements=reqs,
                    status="Open",
                    created_at=datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(5, 30))
                ))
            await db.flush()

        # 8. Candidates
        exist_cand = await db.execute(select(Candidate))
        if exist_cand.scalars().first() is None:
            job_stmt = await db.execute(select(JobOpening))
            all_jobs = job_stmt.scalars().all()
            if all_jobs:
                candidates_data = [
                    ("Rohan", "Mehta", "rohan.mehta@gmail.com", "9876543210"),
                    ("Sneha", "Reddy", "sneha.reddy@yahoo.com", "9876543211"),
                    ("Vikram", "Grover", "vikram.grover@outlook.com", "9876543212"),
                    ("Ananya", "Sen", "ananya.sen@gmail.com", "9876543213"),
                    ("Arjun", "Malhotra", "arjun.m@gmail.com", "9876543214"),
                    ("Priya", "Nair", "priya.nair@hotmail.com", "9876543215"),
                    ("Deepak", "Chawla", "deepak.c@gmail.com", "9876543216"),
                    ("Aisha", "Khan", "aisha.k@gmail.com", "9876543217"),
                    ("Kunal", "Shah", "kunal.shah@gmail.com", "9876543218"),
                    ("Isha", "Verma", "isha.v@gmail.com", "9876543219")
                ]
                for fname, lname, email, phone in candidates_data:
                    job = random.choice(all_jobs)
                    db.add(Candidate(
                        first_name=fname,
                        last_name=lname,
                        email=email,
                        phone=phone,
                        job_id=job.job_id,
                        status=random.choice(["Applied", "Screening", "Interviewing", "Offered", "Rejected"]),
                        resume_url=f"http://yottaflex.com/resumes/{fname.lower()}_{lname.lower()}.pdf",
                        applied_at=datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(1, 15))
                    ))
                await db.flush()

        # 9. Tickets
        exist_tix = await db.execute(select(Ticket))
        if exist_tix.scalars().first() is None:
            categories = ["HR", "IT Support", "Facilities"]
            subjects = {
                "HR": ["Clarification on leave policy", "Salary slip discrepancy", "Address update request"],
                "IT Support": ["VPN connection issue", "Request for new monitor", "Software installation request"],
                "Facilities": ["AC not working in bay 4", "Access card replacement", "Parking permit request"]
            }
            for _ in range(25):
                emp = random.choice(employees)
                cat = random.choice(categories)
                sub = random.choice(subjects[cat])
                db.add(Ticket(
                    employee_id=emp.employee_id,
                    category=cat,
                    subject=sub,
                    description=f"Dear team, I am raising this ticket regarding {sub.lower()}. Please resolve this at the earliest. Thanks.",
                    status=random.choices(["Open", "In Progress", "Resolved", "Closed"], weights=[30, 35, 25, 10])[0],
                    priority=random.choice(["Low", "Medium", "High"]),
                    created_at=datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(1, 20))
                ))
            await db.flush()

        # 10. Policy Documents
        exist_pol = await db.execute(select(PolicyDocument))
        if exist_pol.scalars().first() is None:
            policies = [
                ("Work From Home Policy", "HR Policy", "Employees are allowed to work from home up to 2 days per week with manager approval. Core hours of operation are 10:00 AM to 4:00 PM. High-speed internet is required.", "2.0"),
                ("Annual Leave Policy", "HR Policy", "Employees receive 15 days of vacation leave, 12 days of sick leave, and 10 casual leaves annually. Leave balance does not roll over to the next year. Approved by HR.", "1.1"),
                ("IT Security Guidelines", "IT Guide", "Never share passwords. Always lock your screen when leaving your desk. Use the company VPN when working remotely. Report phishing emails immediately.", "3.0"),
                ("Travel & Expense Policy", "Travel Policy", "Business travel expenses up to $100 per day for meals are reimbursable. Flights must be booked at least 14 days in advance. Receipts must be uploaded.", "1.5"),
                ("Performance Review SOP", "HR Policy", "Performance reviews are conducted bi-annually. Self-evaluation is required. Ratings range from 1 (Needs Improvement) to 5 (Outstanding).", "2.1")
            ]
            for title, cat, content, ver in policies:
                db.add(PolicyDocument(
                    title=title,
                    category=cat,
                    content=content,
                    version=ver,
                    last_updated=datetime.datetime.utcnow()
                ))
            await db.flush()

        await db.commit()
        print("Yottaflex database seeded and entries populated successfully.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_data())
