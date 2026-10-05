# FastAPI backend

This backend is the infrastructure foundation for AI-Knowledge-Chatbot. It
currently provides typed settings, application logging, CORS configuration,
central API routing, safe global exception handling, and a health endpoint.

AI models, RAG, LlamaIndex, ChromaDB, Ollama, Supabase, authentication,
knowledge ingestion, and conversation logic are intentionally not implemented.

## Architecture

```text
backend/
├── app/
│   ├── api/
│   │   ├── health.py       # Health route
│   │   └── router.py       # Central API router
│   ├── core/
│   │   ├── config.py       # Pydantic Settings configuration
│   │   └── logging.py      # Console and file logging
│   ├── database/           # Reserved for future persistence infrastructure
│   ├── middleware/
│   │   └── exceptions.py   # Safe unexpected-error response
│   ├── models/             # Reserved for future domain models
│   ├── schemas/            # Reserved for future API schemas
│   ├── services/           # Reserved for future application services
│   ├── utils/              # Reserved for future shared utilities
│   └── main.py             # FastAPI application assembly
├── tests/
│   └── test_health.py      # Health endpoint test
├── logs/                   # Created automatically at runtime
├── .env.example
└── requirements.txt
```

Each package contains an `__init__.py` marker. Empty extension packages are
kept ready for later features without adding placeholder business logic.

## Configuration

`app/core/config.py` uses Pydantic Settings to load typed values from process
environment variables and a local `.env` file when present. The settings object
is cached as a process-wide singleton. Copy `.env.example` to `.env` only for
local configuration; keep real credentials out of Git.

The application can start with blank external-service settings because no
external service is connected in this phase. Ollama and Supabase values are
configuration placeholders only.

## Logging

The application configures console and file handlers during startup. Logs are
written to `backend/logs/app.log`, which is created automatically and ignored by
Git. Each record includes a timestamp, level, module name, and message. Debug
logging is enabled only when `DEBUG=True` is supplied through configuration.

## Installation

From the `backend` directory, use a Python 3.11+ interpreter:

```text
python -m venv .venv
```

Activate the virtual environment through your IDE or operating system's
environment support, then run:

```text
python -m pip install -r requirements.txt
```

No GPU, model download, database account, or external service is required for
this backend foundation.

## Run the API

With the virtual environment active and the current directory set to `backend`:

```text
uvicorn app.main:app --reload
```

The API listens at `http://127.0.0.1:8000` by default. The development CORS
configuration allows the frontend at `http://localhost:3000` and
`http://127.0.0.1:3000`.

## Health endpoint and API docs

`GET /health` returns HTTP 200:

```json
{
  "status": "healthy",
  "service": "AI Knowledge Chatbot Backend"
}
```

FastAPI automatically exposes:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- OpenAPI schema: `http://127.0.0.1:8000/openapi.json`

## Tests

From the `backend` directory with the virtual environment active:

```text
pytest
```

The test suite exercises `GET /health`, including its HTTP status and response
body.
