# FastAPI backend, local RAG, and Supabase application layer

This backend provides the production foundation for AI-Knowledge-Chatbot. It
uses Ollama for Qwen3.5-4B, LlamaIndex adapters for local generation and
BGE-M3 embeddings, persistent ChromaDB for knowledge vectors, and Supabase for
authenticated application data.

The implementation does not use OpenAI or require `OPENAI_API_KEY`. The
LlamaIndex meta-package is intentionally omitted because it installs OpenAI
integrations; the project installs `llama-index-core` and only local Ollama,
HuggingFace, and Chroma integrations.

## Architecture

```text
backend/
├── app/
│   ├── api/
│   │   ├── auth.py         # Supabase registration, login, and /me
│   │   ├── chat.py         # Authenticated grounded chat and AI health
│   │   ├── documents.py    # Authenticated upload and indexing
│   │   ├── health.py       # Basic backend health route
│   │   └── router.py       # Central API router
│   ├── core/
│   │   ├── config.py       # Typed environment settings
│   │   └── logging.py      # Console and file logging
│   ├── database/
│   │   ├── models.py       # Typed application records
│   │   ├── repository.py   # Supabase data access
│   │   └── supabase_client.py
│   ├── middleware/
│   │   └── exceptions.py   # Safe authentication and error responses
│   ├── services/
│   │   ├── auth/
│   │   │   ├── auth_dependency.py
│   │   │   └── auth_service.py
│   │   ├── ai/             # LLM, embeddings, prompts, RAG, retrieval
│   │   ├── ingestion/      # Loaders, OCR, chunking, and background indexing
│   │   └── vector/         # Persistent ChromaDB adapter
│   └── main.py             # FastAPI application assembly
├── tests/
├── chroma_db/              # Created automatically; ignored by Git
├── logs/                   # Created automatically at runtime
├── .env.example
└── requirements.txt
```

Uploaded source files are stored in the project-level `../knowledge_base/`
directory; vectors are stored in `backend/chroma_db/`. Supabase PostgreSQL
stores profiles, conversations, messages, request logs, and document metadata
only. It does not store embeddings. See `../docs/database_schema.md` and
`../supabase/migrations/001_initial_schema.sql` for the schema and RLS setup.

## AI request flow

```text
Document → loader/OCR → recursive chunks → BGE-M3 (CPU)
         → ChromaDB → retriever → strict context prompt → Qwen3.5 via Ollama
         → grounded answer and source metadata
```

Documents are indexed independently. Adding a document creates or updates its
vector records; no model retraining is required. If retrieval finds no relevant
chunks, the service returns `I could not find this information in the knowledge
base.` without calling Qwen.

## Installation with Conda

Use the existing `cenv` environment with Python 3.11 or newer:

```text
conda activate cenv
python --version
python -m pip install -r requirements.txt
```

BGE-M3 is loaded lazily on CPU. OCR also requires a local Tesseract executable
in addition to the Python `pytesseract` package.

## Supabase setup

1. Create a Supabase project.
2. Open Supabase Dashboard → **SQL Editor**, paste the complete contents of
   `supabase/migrations/001_initial_schema.sql`, and click **Run**. Confirm
   that `profiles`, `conversations`, `messages`, `logs`, and `documents` appear
   under **Table Editor**. Alternatively, apply the migration through the
   Supabase CLI.
   To verify the migration from SQL Editor, run:

   ```sql
   select table_schema, table_name
   from information_schema.tables
   where table_schema = 'public'
     and table_name in ('profiles', 'conversations', 'messages', 'logs', 'documents');
   ```

   If the tables exist but PostgREST still reports `PGRST205`, run
   `notify pgrst, 'reload schema';` once in SQL Editor and restart the backend.
3. Copy `backend/.env.example` to `backend/.env` and set
   `SUPABASE_URL`, `SUPABASE_ANON_KEY`, and `SUPABASE_SERVICE_KEY`. The service
   key is server-only and must never be sent to the frontend.
4. `SUPABASE_JWT_SECRET` may remain empty. The backend asks Supabase Auth to
   verify access tokens, so current Supabase signing algorithms are supported.

Registration and password login use Supabase Auth. The API returns the access
token, and protected routes read it from `Authorization: Bearer <token>`. Chat
and document routes require authentication. Invalid, expired, or unavailable
authentication returns `{ "success": false, "message": "Authentication failed" }`.

## Local Ollama setup

Install Ollama, then pull and start the configured model:

```text
ollama pull qwen3.5:4b
ollama serve
```

Set `OLLAMA_BASE_URL` and `OLLAMA_MODEL` in `backend/.env` when using a
non-default endpoint or model. No OpenAI key is needed.

## Run the backend

From `backend` with `cenv` active:

```text
uvicorn app.main:app --reload
```

The API listens at `http://127.0.0.1:8000`. FastAPI documentation is available
at `/docs`, `/redoc`, and `/openapi.json`.

## API flow

Authentication endpoints are `POST /api/auth/register`,
`POST /api/auth/login`, and protected `GET /api/auth/me`.

Start a conversation by sending a question without an ID:

```json
POST /api/chat
Authorization: Bearer <access_token>
{
  "question": "What is the refund policy?",
  "conversation_id": null
}
```

The response includes `conversation_id`. Send that ID on subsequent requests;
the backend reads at most the last ten messages, retrieves document context,
generates the answer, and stores both messages. The response also includes
`response_time_ms` and source excerpts so the frontend can show latency and
open the retrieved context. Sources are grouped by filename; `pages` contains
all matching pages, `similarity_percent` contains the strongest matching
chunk's score, and `context` contains the combined retrieved excerpts.
`GET /api/chat/conversations` lists the signed-in
user’s recent chats and `GET /api/chat/conversations/{conversation_id}` loads
one after a later login. Every chat request also writes the user, endpoint,
safe question metadata, response time, and success status to `logs`.

For lower local latency, the Ollama adapter keeps the model warm for ten
minutes, disables optional thinking, and uses a 3072-token context window.
Recent conversation memory is limited to 800 characters; retrieved document
chunks remain intact. Short factual answers use a 128-token budget; summaries
and explanations receive more capacity, while explicit word-count requests
are sized dynamically up to 768 tokens. Adjust
`OLLAMA_KEEP_ALIVE`, `OLLAMA_THINKING`, `OLLAMA_CONTEXT_WINDOW`, and
`OLLAMA_NUM_PREDICT` in `backend/.env` for the target machine. A lower output
ceiling may cut off longer answers; enable thinking for complex reasoning
when the additional latency is acceptable.

Index a supported PDF, TXT, DOCX, HTML, PNG, JPG, or JPEG with:

```text
POST /api/documents/index
Authorization: Bearer <access_token>
Content-Type: multipart/form-data
file=<document.pdf>
```

The upload endpoint returns `202 Accepted` and a `job_id` immediately. CPU-heavy
BGE-M3 embedding continues in the background. Poll
`GET /api/documents/index/{job_id}` with the same bearer token until the status
is `completed` or `failed`; a completed job is searchable in the next chat
request. Image files additionally require a local Tesseract installation.

## Tests

Run the suite from `backend` with `cenv` active:

```text
pytest
```

The tests use deterministic fakes for model and Supabase boundaries, so they do
not need an Ollama server or real credentials. Chroma integration tests use a
temporary local collection when ChromaDB is installed.
