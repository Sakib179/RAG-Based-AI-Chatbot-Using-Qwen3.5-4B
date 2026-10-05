# Supabase application schema

Supabase PostgreSQL stores application metadata, user profiles, conversation
messages, request logs, and document metadata. ChromaDB remains the persistent
vector database for chunk text and embeddings; embeddings are not copied into
PostgreSQL.

## Tables

| Table | Columns | Purpose |
| --- | --- | --- |
| `profiles` | `id uuid`, `email text`, `role text`, `created_at timestamptz` | Application profile; `id` references `auth.users.id` |
| `conversations` | `id uuid`, `user_id uuid`, `title text`, `created_at timestamptz`, `updated_at timestamptz` | A user's chat session; `user_id` references `profiles.id` |
| `messages` | `id uuid`, `conversation_id uuid`, `role text`, `content text`, `sources jsonb`, `created_at timestamptz` | Ordered conversation messages; `conversation_id` references `conversations.id` |
| `logs` | `id uuid`, `user_id uuid`, `endpoint text`, `request_data jsonb`, `response_time float`, `success boolean`, `created_at timestamptz` | Backend activity logs; `user_id` optionally references `profiles.id` |
| `documents` | `id uuid`, `filename text`, `file_type text`, `uploaded_by uuid`, `created_at timestamptz` | Knowledge-base metadata; `uploaded_by` references `profiles.id` |

All tables have UUID primary keys where appropriate and UTC `timestamptz`
creation timestamps. Foreign keys use cascading deletion for user-owned data;
logs keep their record when a user is removed.

## Row-level security

The migration enables RLS on every application table and adds ownership-based
policies. Policies never grant unrestricted `using (true)` access. The backend
uses the Supabase service role only on the server, so it can perform repository
operations after independently verifying the user's bearer token. Never expose
the service key to the frontend.

Run `supabase/migrations/001_initial_schema.sql` in the Supabase SQL editor or
through the Supabase CLI before using the authenticated endpoints.
