-- WatAIOliver Supabase Setup Script
-- Run this in your Supabase SQL Editor: https://supabase.com/dashboard/project/zeyggksxsfrqziseysnr/sql/new

-- Enable the vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the document_embeddings table
CREATE TABLE IF NOT EXISTS document_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    content TEXT NOT NULL,
    metadata JSONB,
    embedding vector(768)  -- new
);
-- embedding vector(512)  -- old commented

-- Create an index for vector similarity search
CREATE INDEX IF NOT EXISTS document_embeddings_embedding_idx 
ON document_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Create the match_documents function for vector similarity search
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(512),
    match_threshold float DEFAULT 0.5,
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE SQL STABLE
AS $$
    SELECT 
        id,
        content,
        metadata,
        1 - (embedding <=> query_embedding) AS similarity
    FROM document_embeddings
    WHERE 1 - (embedding <=> query_embedding) > match_threshold
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;

-- Insert some test data (optional)
INSERT INTO document_embeddings (content, metadata, embedding) VALUES 
(
    'This is a test document about artificial intelligence and machine learning.',
    '{"source": "test", "type": "sample"}',
    array_fill(0.1, ARRAY[512])::vector
),
(
    'Vector databases are useful for similarity search and RAG systems.',
    '{"source": "test", "type": "sample"}',
    array_fill(0.2, ARRAY[512])::vector
),
(
    'Supabase provides PostgreSQL with vector extensions for AI applications.',
    '{"source": "test", "type": "sample"}',
    array_fill(0.3, ARRAY[512])::vector
)
ON CONFLICT (id) DO NOTHING;

-- Grant necessary permissions
GRANT ALL ON document_embeddings TO authenticated;
GRANT ALL ON document_embeddings TO anon;

-- Show table structure
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'document_embeddings'
ORDER BY ordinal_position;

-- Test the match_documents function
SELECT 
    id,
    content,
    similarity
FROM match_documents(
    array_fill(0.15, ARRAY[512])::vector,
    0.0,
    3
);

-- Success message
SELECT 'Supabase setup completed successfully!' AS status; 