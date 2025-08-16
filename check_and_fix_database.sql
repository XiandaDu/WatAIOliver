-- Simple script to check and fix the database issue

-- Step 1: Check current courses table structure
SELECT 'Current courses table structure:' as info;
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'courses'
ORDER BY ordinal_position;

-- Step 2: Add custom_models column if missing
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'courses' 
    AND column_name = 'custom_models'
  ) THEN
    -- Add the column
    ALTER TABLE public.courses 
    ADD COLUMN custom_models JSONB DEFAULT '[]'::jsonb;
    
    -- Add index for performance
    CREATE INDEX IF NOT EXISTS idx_courses_custom_models 
    ON public.courses USING gin (custom_models);
    
    RAISE NOTICE 'Successfully added custom_models column';
  ELSE
    RAISE NOTICE 'custom_models column already exists';
  END IF;
END $$;

-- Step 3: Verify the column was added
SELECT 'After adding custom_models column:' as info;
SELECT column_name, data_type, column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'courses'
AND column_name = 'custom_models';

-- Step 4: Test with a sample course (optional - uncomment and replace course_id)
-- UPDATE public.courses 
-- SET custom_models = '[{"name": "Test Model", "api_key": "test-key", "model_type": "openai", "created_at": "2024-01-15T10:30:00Z"}]'::jsonb
-- WHERE course_id = 'your-actual-course-id-here';

SELECT 'Setup complete! You can now test adding custom models.' as result;
