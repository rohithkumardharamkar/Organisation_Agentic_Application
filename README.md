# Organisation_Agentic_Application

Organisation_Agentic_Application is a full-stack agentic workforce operations platform. In the current product flow, the app is presented as **Yottaflex Workforce OS**: a role-aware workspace for HR teams, reporting managers, process engineers, and employees, with an AI copilot layered on top of workforce data and business workflows.

The repository contains:

- A **FastAPI backend** for authentication, dashboards, timesheets, knowledge management, AI operations, and evaluation runs
- A **React + Vite frontend** for role-based dashboards and operational workflows
- An **agent orchestration layer** built around LangGraph/LangChain
- A **local evaluation harness** for measuring routing, tool usage, RAG quality, and task success

## Core capabilities

- Role-based login and protected navigation
- Workforce, talent, project, and executive dashboard views
- AI copilot with streamed responses and approval-aware workflow support
- Timesheet submission, leave management, and manager approval flows
- Knowledge-base upload, indexing, listing, and deletion
- AI operations telemetry, approval queues, and metrics
- Offline agent evaluation suite with stored run results

## Product modules

The frontend currently exposes these major product areas:

- `Executive Command` for high-level HR and leadership metrics
- `Workforce Intel` for workforce health and staffing visibility
- `Project Intel` for project-level operational tracking
- `Talent Intel` for hiring and people insights
- `Timesheet` for employee time entry and leave workflows
- `Manager Approvals` for approvals and exception handling
- `Process Engineering` for process reports and operational controls
- `Data Directory` for organizational documents
- `AI Copilot` for conversational assistance
- `AI Operations` for audit-style visibility into AI actions

## Architecture

### Backend

- **Framework:** FastAPI
- **Database:** SQLite with SQLAlchemy async engine
- **Agent stack:** LangChain, LangGraph, Groq-backed LLM calls
- **Document retrieval:** local uploads + Qdrant-backed indexing
- **Auth:** JWT-style bearer token flow with role-based access checks
- **Evaluation:** dataset-driven evaluation runner with persisted results

### Frontend

- **Framework:** React 19 + TypeScript + Vite
- **State/data:** React Query + Axios
- **Routing:** React Router
- **UI:** Tailwind CSS, Lucide icons, Framer Motion, Recharts

## Repository layout

```text
.
├── backend
│   ├── requirements.txt
│   └── app
│       ├── api/                # FastAPI route modules
│       ├── evaluation/         # Evaluation datasets and runners
│       ├── models/             # SQLAlchemy models
│       ├── repositories/       # Persistence helpers
│       ├── schemas/            # Request/response schemas
│       ├── services/           # Chat, reporting, Qdrant, prediction services
│       ├── src/
│       │   ├── agents/         # Agent routing/orchestration
│       │   ├── core/           # Config, DB, security, seed logic
│       │   ├── memory/         # Memory modules
│       │   ├── models/         # Evaluation + operational DB models
│       │   ├── observability/  # LangSmith hooks
│       │   ├── tools/          # Agent tools
│       │   └── workflow/       # Graph workflow
│       ├── main.py             # FastAPI app entry point
│       └── test_*.py           # Backend tests
├── frontend
│   ├── src
│   │   ├── components/
│   │   ├── context/
│   │   ├── lib/
│   │   └── pages/
│   └── package.json
└── README.md
```

## Getting started

### Prerequisites

- Python 3.10+
- Node.js 20+
- npm 10+

### Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp app/.env.example app/.env
cd app
uvicorn main:app --reload --port 8000
```

What happens on startup:

- database tables are created automatically
- lightweight schema upgrades are applied for uploaded document fields
- seed data is loaded for local development

Backend base URL:

```text
http://localhost:8000
```

API root:

```text
http://localhost:8000/api/v1
```

### Frontend setup

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend default URL:

```text
http://localhost:5173
```

Note: the frontend API client is currently hardcoded to `http://localhost:8000/api/v1` in `frontend/src/lib/api.ts`.

## Environment variables

The backend loads environment variables from `backend/app/.env`.

Minimum local configuration:

```env
GROQ_API_KEY=
EMAIL_USER=
EMAIL_PASSWORD=
DATABASE_URL=sqlite+aiosqlite:///./data/database.db
```

Useful optional settings supported by the backend config:

- `LANGSMITH_API_KEY`
- `LANGCHAIN_TRACING_V2`
- `LANGCHAIN_PROJECT`
- `OLLAMA_URL`
- `OLLAMA_MODEL`
- `LOCAL_OLLAMA_URL`
- `EMAIL_HOST`
- `EMAIL_PORT`

## Main API areas

The backend currently exposes routes for:

- `/auth` - signup, login, mock Google login, mock OTP login, forgot password
- `/copilot` - chat history, status, streamed chat, approval continuation
- `/dashboards` - executive, workforce, projects, talent, role-based views
- `/workforce` - employee and project data
- `/timesheets` - timesheets, bulk entry, stats, leave flows, approvals
- `/process` - process report creation and retrieval
- `/knowledge` - document upload, listing, and deletion
- `/ai-ops` - activity feed, approvals, registry, metrics
- `/evaluations` - evaluation run orchestration and results lookup

## Agent and evaluation flow

The copilot stack uses the `backend/app/src` modules for routing, memory, tools, and workflow execution.

Highlights:

- chat responses are streamed from the backend using server-sent events
- approval-required steps can pause and resume through the `/copilot/approve` flow
- evaluation datasets live in `backend/app/evaluation/dataset`
- evaluation runs write summary and per-case metrics into SQLite tables

## Testing and validation

### Backend tests

From `backend/app`:

```bash
pytest test_api_new.py test_hr_tools.py test_workforce_api.py
```

### Frontend checks

From `frontend`:

```bash
npm run build
npm run lint
```

## Implementation notes

- Knowledge-base upload and delete actions are restricted to the `HR` role.
- The current Google login and OTP login flows are mock/local-development implementations.
- SQLite is used for local persistence; generated DB files are intentionally ignored in Git.
- Uploaded documents and vector-store data are local runtime artifacts and should not be committed.

## Suggested next improvements

- Move the frontend API base URL to environment configuration
- Replace mock social/OTP auth with production identity providers
- Add deployment profiles for Postgres and managed vector storage
- Expand automated tests for copilot approval and knowledge RAG flows

## License

No license has been defined yet.
