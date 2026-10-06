# AI-Knowledge-Chatbot

## Project overview

AI-Knowledge-Chatbot is a local AI-powered knowledge chatbot foundation. The
project includes the frontend skeleton, production-oriented FastAPI backend,
local document ingestion, embeddings, ChromaDB retrieval, Ollama RAG, and
Supabase application data/authentication.

Development happens on macOS, with final execution and testing planned for
Windows. Paths and setup commands are relative and platform independent.
The AI layer uses CPU-friendly inference by default and does not require CUDA.

## Planned architecture

The future frontend will call the FastAPI backend. The backend coordinates
document ingestion, CPU embeddings, ChromaDB retrieval, and Qwen3.5-4B through
Ollama. Supabase PostgreSQL stores application metadata and Supabase Auth
provides identity; ChromaDB remains the vector database.

| Directory | Responsibility |
| --- | --- |
| `frontend/src/app/` | App Router auth and chat pages |
| `frontend/src/components/` | Reusable auth, chat, and UI components |
| `frontend/src/hooks/` | Supabase Auth state and actions |
| `frontend/src/lib/` | Browser Supabase client |
| `frontend/src/services/` | Axios and FastAPI service clients |
| `frontend/src/types/` | Strict frontend API and domain types |
| `frontend/src/providers/` | React Query and theme providers |
| `backend/app/core/` | Typed configuration and application infrastructure |
| `backend/app/api/` | Authentication, chat, document, and health routes |
| `backend/app/middleware/` | Cross-cutting request and error handling |
| `backend/app/services/` | AI, ingestion, and vector services |
| `backend/app/models/` | Future domain and persistence models |
| `backend/app/schemas/` | Future request and response schemas |
| `backend/app/database/` | Supabase client, typed records, and repositories |
| `backend/app/utils/` | Future shared backend utilities |
| `docs/` | Future architecture and operational documentation |
| `scripts/` | Future cross-platform development utilities |
| `knowledge_base/` | Indexed source documents; contents are ignored by Git |

Python package markers and `.gitkeep` files preserve otherwise empty directories
in Git. They contain no feature logic.

## Technology stack

| Layer | Technology | Current status |
| --- | --- | --- |
| Frontend | Next.js, React, TypeScript, App Router, Tailwind CSS, ESLint | Tooling and root layout configured; no pages |
| Backend | FastAPI, Python 3.11+, Uvicorn | Configuration, logging, RAG services, indexing, chat, CORS, and errors |
| Local LLM | Qwen3.5-4B through Ollama | Implemented through a lazy local adapter |
| Embeddings | BAAI/bge-m3 | Implemented with CPU execution |
| RAG framework | LlamaIndex core and local integrations | Implemented |
| Vector database | ChromaDB | Implemented with persistent local storage |
| Relational database | Supabase PostgreSQL | Application data integrated |
| Authentication | Supabase Auth | Bearer-token flow integrated |

Target runtime hardware: Intel i5-13600KF, GTX 1650 with 4 GB VRAM, and 16 GB
RAM. The local AI adapters use CPU execution by default; no CUDA dependency or
GPU acceleration is required.

## Development roadmap

1. **Foundation:** establish directories, tooling, environment templates,
   documentation, Git, and backend infrastructure.
2. **Local RAG layer (this step):** add ingestion, OCR, embeddings, ChromaDB,
   retrieval, Ollama generation, and grounded API endpoints.
3. **Chatbot experience:** implement frontend pages and conversation UI.
4. **Production preparation:** expand API documentation, add tests for features,
   and validate deployment and operation on Windows.

## Local development

### Prerequisites

- Node.js 20.9+ and npm; use a supported Node.js LTS release.
- Python 3.11+ and pip.
- Git.

The frontend dependency versions are recorded in `frontend/package-lock.json`.
Backend runtime dependencies are pinned in `backend/requirements.txt`.

### Frontend application

From the project root:

```text
cd frontend
npm install
npm run dev
```

Create `frontend/.env` from `frontend/.env.example` and set the public Supabase
URL and anon key plus the FastAPI URL. The server listens at
`http://localhost:3000`; `/login`, `/register`, and protected `/chat` are
available.

Authentication uses the browser Supabase client. Supabase persists and refreshes
the session; the Axios request interceptor reads the current access token and
sends `Authorization: Bearer <token>` to FastAPI. Chat requests go only to
`/api/chat`; the browser never calls Ollama or ChromaDB and never receives the
Supabase service key.

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
conda activate cenv
python --version
```

Confirm that `python --version` reports Python 3.11 or newer before continuing.
The following commands install dependencies into the existing `cenv` Conda
environment:

```text
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/health` to receive:

```json
{"status": "healthy", "service": "AI Knowledge Chatbot Backend"}
```

FastAPI's generated Swagger UI is at `http://127.0.0.1:8000/docs`, ReDoc is at
`http://127.0.0.1:8000/redoc`, and the OpenAPI schema is at
`http://127.0.0.1:8000/openapi.json`. The backend AI setup and API examples are
documented in [`backend/README.md`](backend/README.md). Use `--reload` for
development only.

### Environment templates and Supabase setup

The root `.env.example` and `backend/.env.example` contain templates only. The
backend reads environment variables and an optional local `.env` file at startup.
Keep server secrets in backend configuration and never expose the
Supabase service key to the browser.

Create a Supabase project, run `supabase/migrations/001_initial_schema.sql`,
and set the Supabase variables in `backend/.env` before using authentication,
document indexing, or chat. The service key is server-only. See
[`backend/README.md`](backend/README.md) and
[`docs/database_schema.md`](docs/database_schema.md) for the setup and schema.

The frontend only needs these public values in `frontend/.env`:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

Official setup references: [Next.js](https://nextjs.org/docs/app/getting-started/installation),
[Tailwind CSS](https://tailwindcss.com/docs/installation/framework-guides/nextjs),
and [FastAPI / Uvicorn](https://fastapi.tiangolo.com/deployment/manually/).

## License

MIT. See [LICENSE](LICENSE).
