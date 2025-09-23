CREATE TABLE ab_test_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL,
    user_id UUID REFERENCES auth.users(id),
    course_id UUID,
    interaction_mode VARCHAR(20) CHECK (interaction_mode IN ('daily',
'problem_solving')) NOT NULL,
    original_query TEXT NOT NULL,
    prompt_variant_a TEXT NOT NULL,
    prompt_variant_b TEXT NOT NULL,
    response_a TEXT NOT NULL,
    response_b TEXT NOT NULL,
    chosen_response_id VARCHAR(1) CHECK (chosen_response_id IN ('A', 'B')),
    feedback_text TEXT,
    model_used VARCHAR(100),
    latency_a INTEGER,
    latency_b INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    feedback_submitted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_ab_test_logs_query_id ON ab_test_logs(query_id);
CREATE INDEX idx_ab_test_logs_user_id ON ab_test_logs(user_id);
CREATE INDEX idx_ab_test_logs_course_id ON ab_test_logs(course_id);
CREATE INDEX idx_ab_test_logs_interaction_mode ON ab_test_logs(interaction_mode);