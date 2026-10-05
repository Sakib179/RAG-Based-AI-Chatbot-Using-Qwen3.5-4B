# Backend foundation

Python 3.11+ and FastAPI provide the API foundation. Only the application entry
point and `GET /health` are implemented. Uvicorn is the server; no optional
server extras, AI packages, database drivers, or authentication dependencies
are installed.

## Package structure

- `app/main.py`: initializes FastAPI and exposes the health endpoint.
- `app/config/`: reserved for future settings.
- `app/api/`: reserved for future API routers.
- `app/services/`: reserved for future application services.
- `app/models/`: reserved for future domain and persistence models.
- `app/schemas/`: reserved for future request and response schemas.
- `app/database/`: reserved for future database access.
- `app/utils/`: reserved for future shared utilities.

Empty `__init__.py` files mark these directories as Python packages. There are
no settings loaders, authentication, database connections, AI/RAG logic,
ingestion, conversations, or logging implementations yet.

## Run locally

From `backend/`, using a Python 3.11+ interpreter:

```text
python -m venv .venv
```

Select and activate `.venv` through your IDE or shell's virtual environment
support, then open a terminal using that environment. In the following commands,
`python` must refer to the environment's Python 3.11+ interpreter:

```text
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

`--reload` is for development. No GPU, external service, or environment file
is needed to start the skeleton.

## Available endpoints

| URL | Purpose |
| --- | --- |
| `http://127.0.0.1:8000/health` | Returns HTTP 200 with `{"status": "healthy"}` |
| `http://127.0.0.1:8000/docs` | FastAPI-generated Swagger UI |
| `http://127.0.0.1:8000/redoc` | FastAPI-generated ReDoc documentation |
| `http://127.0.0.1:8000/openapi.json` | FastAPI-generated OpenAPI schema |

The generated API documentation currently describes only the health endpoint.
It is part of FastAPI initialization, not a separate application feature.

## Environment template

`.env.example` contains blank placeholders for future configuration. It is not
loaded by this skeleton. No real credentials are included. Supabase and Ollama
setup instructions will be added when their integrations are implemented.
