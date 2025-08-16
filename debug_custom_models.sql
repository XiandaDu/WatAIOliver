-- Debug script to check if custom_models column exists and test functionality

-- 1. Check if custom_models column exists in courses table
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'courses' 
AND column_name = 'custom_models';

-- 2. Show current structure of courses table
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'courses'
ORDER BY ordinal_position;

-- 3. Check if any courses exist and their structure
SELECT course_id, title, 
       CASE 
         WHEN custom_models IS NULL THEN 'NULL'
         ELSE custom_models::text
       END as custom_models_value
FROM public.courses 
LIMIT 5;

-- 4. Test adding custom_models column if it doesn't exist
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'courses' 
    AND column_name = 'custom_models'
  ) THEN
    ALTER TABLE public.courses 
    ADD COLUMN custom_models JSONB DEFAULT '[]'::jsonb;
    
    RAISE NOTICE 'Added custom_models column to courses table';
  ELSE
    RAISE NOTICE 'custom_models column already exists';
  END IF;
END $$;

-- 5. Test updating a course with custom_models (replace with actual course_id)
-- UPDATE public.courses 
-- SET custom_models = '[{"name": "Test Model", "api_key": "test-key", "model_type": "openai"}]'::jsonb
-- WHERE course_id = 'your-course-id-here';

-- 6. Verify the update worked
-- SELECT course_id, title, custom_models 
-- FROM public.courses 
-- WHERE course_id = 'your-course-id-here';
