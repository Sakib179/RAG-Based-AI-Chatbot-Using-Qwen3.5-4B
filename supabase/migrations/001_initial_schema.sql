-- Application data schema for Supabase PostgreSQL.
-- ChromaDB remains the vector store; this migration stores metadata only.

create extension if not exists pgcrypto;

create table if not exists public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    email text,
    role text not null default 'user' check (role in ('user', 'admin')),
    created_at timestamptz not null default now()
);

create table if not exists public.conversations (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.profiles(id) on delete cascade,
    title text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.messages (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid not null references public.conversations(id) on delete cascade,
    role text not null check (role in ('user', 'assistant', 'system')),
    content text not null,
    sources jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.logs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid references public.profiles(id) on delete set null,
    endpoint text not null,
    request_data jsonb not null default '{}'::jsonb,
    response_time double precision,
    success boolean not null default true,
    created_at timestamptz not null default now()
);

create table if not exists public.documents (
    id uuid primary key default gen_random_uuid(),
    filename text not null,
    file_type text not null,
    uploaded_by uuid not null references public.profiles(id) on delete cascade,
    created_at timestamptz not null default now()
);

create index if not exists conversations_user_id_idx on public.conversations(user_id);
create index if not exists messages_conversation_id_created_at_idx
    on public.messages(conversation_id, created_at);
create index if not exists logs_user_id_created_at_idx on public.logs(user_id, created_at);
create index if not exists documents_uploaded_by_idx on public.documents(uploaded_by);

-- RLS is enabled with ownership policies only. The backend service role bypasses
-- these policies; browser clients cannot read another user's application data.
alter table public.profiles enable row level security;
alter table public.conversations enable row level security;
alter table public.messages enable row level security;
alter table public.logs enable row level security;
alter table public.documents enable row level security;

create policy profiles_select_own on public.profiles for select
    using (auth.uid() = id);
create policy profiles_insert_own on public.profiles for insert
    with check (auth.uid() = id);
create policy profiles_update_own on public.profiles for update
    using (auth.uid() = id) with check (auth.uid() = id);

create policy conversations_select_own on public.conversations for select
    using (auth.uid() = user_id);
create policy conversations_insert_own on public.conversations for insert
    with check (auth.uid() = user_id);
create policy conversations_update_own on public.conversations for update
    using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy conversations_delete_own on public.conversations for delete
    using (auth.uid() = user_id);

create policy messages_select_own on public.messages for select
    using (exists (
        select 1 from public.conversations c
        where c.id = conversation_id and c.user_id = auth.uid()
    ));
create policy messages_insert_own on public.messages for insert
    with check (exists (
        select 1 from public.conversations c
        where c.id = conversation_id and c.user_id = auth.uid()
    ));

create policy logs_select_own on public.logs for select
    using (auth.uid() = user_id);

create policy documents_select_own on public.documents for select
    using (auth.uid() = uploaded_by);
create policy documents_insert_own on public.documents for insert
    with check (auth.uid() = uploaded_by);
