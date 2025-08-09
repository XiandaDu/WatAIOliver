-- Add courses column to users table (Simple version for TEXT user_id)
-- Run this SQL in your Supabase SQL editor

-- Add courses column as an array of course IDs
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS courses TEXT[] DEFAULT '{}';

-- Create an index for better performance when querying by courses
CREATE INDEX IF NOT EXISTS idx_users_courses ON users USING GIN (courses);

-- Create a function to add a course to a user
CREATE OR REPLACE FUNCTION add_course_to_user(user_uuid TEXT, course_id TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE users 
    SET courses = array_append(COALESCE(courses, ARRAY[]::TEXT[]), course_id)
    WHERE user_id = user_uuid 
    AND NOT (COALESCE(courses, ARRAY[]::TEXT[]) @> ARRAY[course_id]);
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Create a function to remove a course from a user
CREATE OR REPLACE FUNCTION remove_course_from_user(user_uuid TEXT, course_id TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE users 
    SET courses = array_remove(COALESCE(courses, ARRAY[]::TEXT[]), course_id)
    WHERE user_id = user_uuid;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get all courses for a user
CREATE OR REPLACE FUNCTION get_user_courses(user_uuid TEXT)
RETURNS TEXT[] AS $$
DECLARE
    user_courses TEXT[];
BEGIN
    SELECT COALESCE(courses, ARRAY[]::TEXT[]) INTO user_courses
    FROM users 
    WHERE user_id = user_uuid;
    
    RETURN COALESCE(user_courses, ARRAY[]::TEXT[]);
END;
$$ LANGUAGE plpgsql;

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION add_course_to_user(TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION remove_course_from_user(TEXT, TEXT) TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_courses(TEXT) TO authenticated;

-- Update RLS policies to include courses column
DROP POLICY IF EXISTS "Users can view their own profile" ON users;
CREATE POLICY "Users can view their own profile" ON users
    FOR SELECT USING (auth.uid()::TEXT = user_id);

DROP POLICY IF EXISTS "Users can update their own profile" ON users;
CREATE POLICY "Users can update their own profile" ON users
    FOR UPDATE USING (auth.uid()::TEXT = user_id);

-- Add policy for admins to manage user courses
DROP POLICY IF EXISTS "Admins can manage user courses" ON users;
CREATE POLICY "Admins can manage user courses" ON users
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE user_id = auth.uid()::TEXT 
            AND role = 'admin'
        )
    );

-- Test the functions with a sample user
DO $$
DECLARE
    test_user_id TEXT;
    test_result BOOLEAN;
    test_courses TEXT[];
BEGIN
    -- Get a test user ID
    SELECT user_id INTO test_user_id FROM users LIMIT 1;
    
    IF test_user_id IS NOT NULL THEN
        RAISE NOTICE 'Testing with user ID: %', test_user_id;
        
        -- Test adding a course
        SELECT add_course_to_user(test_user_id, 'test-course-123') INTO test_result;
        RAISE NOTICE 'Add course result: %', test_result;
        
        -- Test getting courses
        SELECT get_user_courses(test_user_id) INTO test_courses;
        RAISE NOTICE 'User courses after adding: %', test_courses;
        
        -- Test removing a course
        SELECT remove_course_from_user(test_user_id, 'test-course-123') INTO test_result;
        RAISE NOTICE 'Remove course result: %', test_result;
        
        -- Test getting courses after removal
        SELECT get_user_courses(test_user_id) INTO test_courses;
        RAISE NOTICE 'User courses after removal: %', test_courses;
    ELSE
        RAISE NOTICE 'No users found for testing. Create a user first.';
    END IF;
END $$;

-- Success message
SELECT 'Courses column added to users table successfully! Functions tested and working.' AS status;
