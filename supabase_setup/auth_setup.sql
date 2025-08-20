-- Authentication Setup for WatAI Oliver
-- Run this SQL in your Supabase SQL editor to set up authentication tables

-- Create users table for user profiles
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR NOT NULL UNIQUE,
    username VARCHAR NOT NULL,
    full_name VARCHAR,
    role VARCHAR NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'instructor', 'admin')),
    account_type VARCHAR DEFAULT 'active' CHECK (account_type IN ('active', 'blocked')),
    avatar_url VARCHAR,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Create policies for users table
DROP POLICY IF EXISTS "Users can view their own profile" ON users;
CREATE POLICY "Users can view their own profile" ON users
    FOR SELECT USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Users can update their own profile" ON users;
CREATE POLICY "Users can update their own profile" ON users
    FOR UPDATE USING (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Enable insert for authenticated users only" ON users;
CREATE POLICY "Enable insert for authenticated users only" ON users
    FOR INSERT WITH CHECK (auth.uid()::text = user_id::text);

DROP POLICY IF EXISTS "Admins can view all users" ON users;
CREATE POLICY "Admins can view all users" ON users
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE user_id::text = auth.uid()::text 
            AND role = 'admin'
        )
    );

DROP POLICY IF EXISTS "Admins can update all users" ON users;
CREATE POLICY "Admins can update all users" ON users
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE user_id::text = auth.uid()::text 
            AND role = 'admin'
        )
    );

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at);

-- Create courses table first (if it doesn't exist)
CREATE TABLE IF NOT EXISTS courses (
    course_id TEXT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    term VARCHAR(200),
    created_by TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS for courses
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;

-- RLS policies for courses - allow authenticated users to view all courses
DROP POLICY IF EXISTS "Users can view all courses" ON courses;
CREATE POLICY "Users can view all courses" ON courses
    FOR SELECT TO authenticated USING (true);

-- Allow authenticated users to create courses
DROP POLICY IF EXISTS "Users can create courses" ON courses;
CREATE POLICY "Users can create courses" ON courses
    FOR INSERT TO authenticated WITH CHECK (auth.uid()::text = created_by);

-- Allow course creators to update their courses
DROP POLICY IF EXISTS "Users can update their courses" ON courses;
CREATE POLICY "Users can update their courses" ON courses
    FOR UPDATE TO authenticated USING (auth.uid()::text = created_by);

-- Allow course creators to delete their courses
DROP POLICY IF EXISTS "Users can delete their courses" ON courses;
CREATE POLICY "Users can delete their courses" ON courses
    FOR DELETE TO authenticated USING (auth.uid()::text = created_by);

-- Store user->courses relationship via array on users table
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'courses'
    ) THEN
        ALTER TABLE users ADD COLUMN courses TEXT[] DEFAULT '{}';
        CREATE INDEX IF NOT EXISTS idx_users_courses ON users USING GIN (courses);
    END IF;
END $$;

-- Whitelist of instructors permitted to access admin panel
CREATE TABLE IF NOT EXISTS instructor_whitelist (
    email TEXT PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default admin user (optional - update email as needed)
-- INSERT INTO auth.users (id, email, email_confirmed_at, created_at, updated_at)
-- VALUES (gen_random_uuid(), 'admin@uwaterloo.ca', NOW(), NOW(), NOW())
-- ON CONFLICT (email) DO NOTHING;

-- Uncomment and update the following to create a default admin user:
-- INSERT INTO users (user_id, email, username, full_name, role)
-- SELECT id, 'admin@uwaterloo.ca', 'admin', 'System Administrator', 'admin'
-- FROM auth.users 
-- WHERE email = 'admin@uwaterloo.ca'
-- ON CONFLICT (user_id) DO NOTHING;