-- First, check how many embeddings exist
SELECT COUNT(*) FROM public.document_embeddings;

-- Extensions
create extension if not exists pgcrypto;
create extension if not exists vector;

-- Users profile table
create table if not exists public.users (
  user_id uuid primary key references auth.users(id) on delete cascade,
  email varchar not null unique,
  username varchar not null,
  full_name varchar,
  role varchar not null default 'student' check (role in ('student','instructor','admin')),
  account_type varchar default 'active' check (account_type in ('active','blocked')),
  avatar_url varchar,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Update trigger
create or replace function public.update_updated_at_column() returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;$$ language plpgsql;

drop trigger if exists update_users_updated_at on public.users;
create trigger update_users_updated_at before update on public.users
for each row execute function public.update_updated_at_column();

alter table public.users enable row level security;

-- Basic policies
drop policy if exists "Users can view their own profile" on public.users;
create policy "Users can view their own profile" on public.users for select using (auth.uid()::text = user_id::text);

drop policy if exists "Users can update their own profile" on public.users;
create policy "Users can update their own profile" on public.users for update using (auth.uid()::text = user_id::text);

drop policy if exists "Enable insert for authenticated users only" on public.users;
create policy "Enable insert for authenticated users only" on public.users for insert with check (auth.uid()::text = user_id::text);

-- Courses
create table if not exists public.courses (
  course_id text primary key,
  title varchar(200) not null,
  description text,
  term varchar(200),
  created_by text,
  prompt text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

alter table public.courses enable row level security;

drop policy if exists "Users can view all courses" on public.courses;
create policy "Users can view all courses" on public.courses for select to authenticated using (true);

drop policy if exists "Users can create courses" on public.courses;
create policy "Users can create courses" on public.courses for insert to authenticated with check (auth.uid()::text = created_by);

drop policy if exists "Users can update their courses" on public.courses;
create policy "Users can update their courses" on public.courses for update to authenticated using (auth.uid()::text = created_by);

drop policy if exists "Users can delete their courses" on public.courses;
create policy "Users can delete their courses" on public.courses for delete to authenticated using (auth.uid()::text = created_by);

-- Add prompt column to courses if it doesn't exist
do $$
begin
  if not exists (select 1 from information_schema.columns 
                 where table_schema = 'public' 
                 and table_name = 'courses' 
                 and column_name = 'prompt') then
    alter table public.courses add column prompt text;
  end if;
end $$;

-- User->courses relationship stored on users table via TEXT[] and helper functions
do $$
begin
  if not exists (select 1 from information_schema.columns 
                 where table_schema = 'public' 
                 and table_name = 'users' 
                 and column_name = 'courses') then
    alter table public.users add column courses text[] default '{}'::text[];
    create index if not exists idx_users_courses on public.users using gin (courses);
  end if;
end $$;

-- Instructor whitelist
create table if not exists public.instructor_whitelist (
  email text primary key,
  created_at timestamptz default now()
);

-- Conversations table (create if not exists, then add missing columns)
create table if not exists public.conversations (
  conversation_id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Add course_id column to conversations if it doesn't exist
do $$
begin
  if not exists (select 1 from information_schema.columns 
                 where table_schema = 'public' 
                 and table_name = 'conversations' 
                 and column_name = 'course_id') then
    alter table public.conversations add column course_id text;
  end if;
end $$;

-- Messages table (create if not exists, then add missing columns)
create table if not exists public.messages (
  message_id uuid primary key default gen_random_uuid(),
  conversation_id uuid not null references public.conversations(conversation_id) on delete cascade,
  user_id uuid,
  sender text not null check (sender in ('user','assistant')),
  content text not null,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Add course_id column to messages if it doesn't exist
do $$
begin
  if not exists (select 1 from information_schema.columns 
                 where table_schema = 'public' 
                 and table_name = 'messages' 
                 and column_name = 'course_id') then
    alter table public.messages add column course_id text;
  end if;
end $$;

-- Add model column to messages if it doesn't exist
do $$
begin
  if not exists (select 1 from information_schema.columns 
                 where table_schema = 'public' 
                 and table_name = 'messages' 
                 and column_name = 'model') then
    alter table public.messages add column model text;
  end if;
end $$;

-- Add foreign key constraints safely (only if they don't exist)
do $$
begin
  if not exists (select 1 from information_schema.table_constraints 
                 where constraint_schema = 'public' 
                 and table_name = 'conversations' 
                 and constraint_name = 'conversations_course_id_fkey') then
    alter table public.conversations 
    add constraint conversations_course_id_fkey 
    foreign key (course_id) references public.courses(course_id) on delete set null;
  end if;
end $$;

do $$
begin
  if not exists (select 1 from information_schema.table_constraints 
                 where constraint_schema = 'public' 
                 and table_name = 'messages' 
                 and constraint_name = 'messages_course_id_fkey') then
    alter table public.messages 
    add constraint messages_course_id_fkey 
    foreign key (course_id) references public.courses(course_id) on delete set null;
  end if;
end $$;

create index if not exists idx_messages_course on public.messages(course_id);
create index if not exists idx_messages_conversation on public.messages(conversation_id);
create index if not exists idx_conversations_course on public.conversations(course_id);

-- Documents (metadata only, not embeddings)
create table if not exists public.documents (
  document_id text primary key,
  course_id text references public.courses(course_id) on delete set null,
  term text,
  title text,
  content text,
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

-- Vector table for embeddings
create table if not exists public.document_embeddings (
  id uuid primary key default gen_random_uuid(),
  content text not null,
  metadata jsonb,
  embedding vector(512)
);

-- Ensure primary key exists (in case table was created without it)
do $$
begin
  if not exists (select 1 from information_schema.table_constraints 
                 where constraint_schema = 'public' 
                 and table_name = 'document_embeddings' 
                 and constraint_type = 'PRIMARY KEY') then
    alter table public.document_embeddings add primary key (id);
  end if;
end $$;

create index if not exists document_embeddings_embedding_idx on public.document_embeddings using ivfflat (embedding vector_cosine_ops) with (lists = 100);
create index if not exists document_embeddings_metadata_idx on public.document_embeddings using gin (metadata);

grant all on public.document_embeddings to authenticated;
grant all on public.document_embeddings to service_role;

-- Analytics RPC: compute course-level message analytics on the DB side
create or replace function public.get_course_analytics_counts(p_course_id text)
returns jsonb
language plpgsql
stable
as $$
declare
  result jsonb;
begin
  with days as (
    select (current_date - i) as d
    from generate_series(6, 0, -1) as i
  ),
  day_counts as (
    select d,
           coalesce((
             select count(*)
             from public.messages m
             where m.course_id = p_course_id
               and m.created_at::date = d
           ), 0) as cnt
    from days
  ),
  totals as (
    select
      (select count(distinct m.conversation_id) from public.messages m where m.course_id = p_course_id) as total_conversations,
      (select count(distinct m.user_id) from public.messages m where m.course_id = p_course_id and m.user_id is not null) as active_users
  ),
  models as (
    select coalesce(model, 'unknown') as model_key, count(*)::int as model_count
    from public.messages
    where course_id = p_course_id and sender = 'assistant'
    group by coalesce(model, 'unknown')
  ),
  day_labels as (
    select jsonb_agg(to_char(d, 'Dy') order by d) as labels
    from day_counts
  ),
  day_counts_agg as (
    select jsonb_agg(cnt order by d) as counts
    from day_counts
  )
  select jsonb_build_object(
    'total_conversations', totals.total_conversations,
    'active_users', totals.active_users,
    'usage_by_day', jsonb_build_object(
      'labels', day_labels.labels,
      'counts', day_counts_agg.counts
    ),
    'conversations_by_model', coalesce((select jsonb_object_agg(model_key, model_count) from models), '{}'::jsonb)
  ) into result
  from totals, day_labels, day_counts_agg;

  return result;
end;
$$;

-- Grant execute permission
grant execute on function public.get_course_analytics_counts(text) to authenticated;
grant execute on function public.get_course_analytics_counts(text) to service_role;