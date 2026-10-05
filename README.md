# AI-Knowledge-Chatbot

## Project overview

AI-Knowledge-Chatbot is the foundation for a planned AI-powered knowledge
chatbot. This step establishes the project structure, frontend tooling, and a
minimal backend. The only application endpoint implemented is `GET /health`.

There are no frontend pages, chatbot features, AI integrations, retrieval
pipelines, authentication, database connections, or document ingestion yet.

Development happens on macOS, with final execution and testing planned for
Windows. Paths and setup commands are relative and platform independent.
The skeleton does not require a GPU or any model downloads.

## Planned architecture

The future frontend will call the FastAPI backend. The backend will coordinate
application services, knowledge ingestion, retrieval, and conversation handling.
Supabase PostgreSQL and Supabase Auth are planned for persistence and identity.
ChromaDB is planned for vector storage; LlamaIndex will coordinate retrieval
using BAAI/bge-m3 embeddings and Qwen3.5-4B served locally through Ollama.
These integrations are documented plans, not implemented capabilities.

| Directory | Responsibility |
| --- | --- |
| `frontend/app/` | App Router layout and future routes |
| `frontend/components/` | Future reusable UI components |
| `frontend/hooks/` | Future reusable React hooks |
| `frontend/lib/` | Future frontend utilities and client helpers |
| `frontend/types/` | Future shared TypeScript types |
| `frontend/public/` | Future static assets |
| `backend/app/config/` | Future application configuration |
| `backend/app/api/` | Future API routers |
| `backend/app/services/` | Future application services |
| `backend/app/models/` | Future domain and persistence models |
| `backend/app/schemas/` | Future request and response schemas |
| `backend/app/database/` | Future database access and migrations |
| `backend/app/utils/` | Future shared backend utilities |
| `docs/` | Future architecture and operational documentation |
| `scripts/` | Future cross-platform development utilities |
| `knowledge_base/` | Future local knowledge documents; contents are ignored by Git |

Python package markers and `.gitkeep` files preserve otherwise empty directories
in Git. They contain no feature logic.

## Technology stack

| Layer | Technology | Current status |
| --- | --- | --- |
| Frontend | Next.js, React, TypeScript, App Router, Tailwind CSS, ESLint | Tooling and root layout configured; no pages |
| Backend | FastAPI, Python 3.11+, Uvicorn | Application and health endpoint only |
| Local LLM | Qwen3.5-4B through Ollama | Planned; not installed or connected |
| Embeddings | BAAI/bge-m3 | Planned; not installed or connected |
| RAG framework | LlamaIndex | Planned; not installed or connected |
| Vector database | ChromaDB | Planned; not installed or connected |
| Relational database | Supabase PostgreSQL | Planned; not connected |
| Authentication | Supabase Auth | Planned; not connected |

Target runtime hardware: Intel i5-13600KF, GTX 1650 with 4 GB VRAM, and 16 GB
RAM. Future AI integration must support CPU execution and be measured on this
hardware; no GPU acceleration or model performance is assumed by this foundation.

## Development roadmap

1. **Foundation (this step):** establish directories, tooling, environment
   templates, documentation, Git, and backend health endpoint.
2. **Configuration and observability:** implement environment validation,
   application logging, and API conventions.
3. **Persistence and identity:** integrate Supabase PostgreSQL and Supabase Auth.
4. **Knowledge ingestion:** add PDF, TXT, DOCX, web content, and image OCR support.
5. **Retrieval and local inference:** integrate embeddings, ChromaDB,
   LlamaIndex, and Ollama with measured CPU and memory usage.
6. **Chatbot experience:** implement UI pages, conversations, and memory.
7. **Production preparation:** expand API documentation, add tests for features,
   and validate deployment and operation on Windows.

## Local development

### Prerequisites

- Node.js 20.9+ and npm; use a supported Node.js LTS release.
- Python 3.11+ and pip.
- Git.

The frontend dependency versions are recorded in `frontend/package-lock.json`.
Backend runtime dependencies are pinned in `backend/requirements.txt`.

### Frontend skeleton

From the project root:

```text
cd frontend
npm ci
npm run dev
```

The server listens at `http://localhost:3000`. No `app/page.tsx` exists, so `/`
returns Next.js's default 404. This is expected until UI pages are implemented.

Available checks and production commands:

```text
npm run lint
npm run typecheck
npm run build
npm start
```

Run `npm start` after a successful build. No external font or model downloads are
required by the application.

### Backend skeleton

In a separate terminal, from the project root:

```text
cd backend
python -m venv .venv
```

Here, `python` means a Python 3.11+ interpreter. Select and activate `.venv`
using your IDE's Python environment support or your shell's virtual environment
support, then open a terminal using that environment. Confirm `python --version`
reports Python 3.11 or newer before continuing:

```text
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/health` to receive:

```json
{"status": "healthy"}
```

FastAPI's generated Swagger UI is at `http://127.0.0.1:8000/docs`, ReDoc is at
`http://127.0.0.1:8000/redoc`, and the OpenAPI schema is at
`http://127.0.0.1:8000/openapi.json`. They document only the health endpoint.
Use `--reload` for development only.

### Environment templates and future setup

The root `.env.example` and `backend/.env.example` contain blank placeholders
only. Neither application reads them in this step, and no `.env` file or
credentials are required to run the skeleton. Keep future server secrets in
backend configuration and never expose the Supabase service key to the browser.

**Placeholder:** complete local setup instructions for Supabase, Ollama, model
downloads, ingestion, and retrieval will be added alongside those features.

Official setup references: [Next.js](https://nextjs.org/docs/app/getting-started/installation),
[Tailwind CSS](https://tailwindcss.com/docs/installation/framework-guides/nextjs),
and [FastAPI / Uvicorn](https://fastapi.tiangolo.com/deployment/manually/).

## License

MIT. See [LICENSE](LICENSE).
