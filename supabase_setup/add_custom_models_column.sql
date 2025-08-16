-- Add custom_models column to courses table
-- This migration adds support for storing custom OpenAI API configurations per course

-- Add custom_models column to courses table if it doesn't exist
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
    
    -- Add a comment to document the column purpose
    COMMENT ON COLUMN public.courses.custom_models IS 'Stores custom OpenAI API configurations for the course';
    
    -- Create an index for better performance when querying custom models
    CREATE INDEX IF NOT EXISTS idx_courses_custom_models 
    ON public.courses USING gin (custom_models);
    
    RAISE NOTICE 'Successfully added custom_models column to courses table';
  ELSE
    RAISE NOTICE 'Column custom_models already exists in courses table';
  END IF;
END $$;

-- Verify the column was added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'courses' 
AND column_name = 'custom_models';
