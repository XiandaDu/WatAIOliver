-- Add invite_code column to courses for 6-digit join codes
-- Run this against your Supabase/Postgres database

ALTER TABLE public.courses
ADD COLUMN IF NOT EXISTS invite_code varchar(6);

-- Optionally, enforce uniqueness for non-null invite codes
-- CREATE UNIQUE INDEX IF NOT EXISTS courses_invite_code_unique
--   ON public.courses (invite_code)
--   WHERE invite_code IS NOT NULL;

-- Optionally backfill invite codes for existing courses (no uniqueness guarantee)
-- UPDATE public.courses
-- SET invite_code = lpad((floor(random()*1000000))::int::text, 6, '0')
-- WHERE invite_code IS NULL;


