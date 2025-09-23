# A/B Testing Module (What Has Been Implemented So Far)
This is in no way official documentation, it's just a guide from the developer who previously worked on this to help whoever works on this next get a better idea of where things are right now (so they hopefully spend less time lost in code). 

What's here, as well as the ideas, intended usage flow, etc. included could change based on the PMs' guidance, so please take the ideas written here with a grain of salt!

Please feel free to tweak, delete, and change as needed!

## Architecture

### Core Components

#### `models.py`
Defines Pydantic models for API requests and responses:
- `ABTestCreateRequest`: Input for creating A/B tests (query, user_id, course_id, interaction_mode)
- `ABTestFeedback`: User feedback submission (query_id, chosen_response_id, feedback_text)
- `ABTestResponse`: API response containing both prompt variants and metadata

#### `router.py`
FastAPI endpoints for A/B testing:
- `POST /api/ab_test/create`: Creates A/B test with two prompt variants
- `POST /api/ab_test/feedback`: Submits user choice and optional feedback

#### `service.py`
Core business logic:
- `create_ab_test_query()`: Generates prompt variants, calls LLM service, stores results
- `submit_ab_test_feedback()`: Records user preferences in database
- `call_llm_service()`: Placeholder for actual LLM service integration

#### `prompt_generator.py`
Prompt variant generation:
- `PromptGenerator.generate_variants()`: Creates detailed vs concise prompt versions
- Supports different prompt styles for A/B testing

## Database Schema

The module uses a `ab_test_logs` table in Supabase with the following structure:

```sql
CREATE TABLE ab_test_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_id UUID NOT NULL,
    user_id UUID REFERENCES auth.users(id),
    course_id UUID,
    interaction_mode VARCHAR(20) CHECK (interaction_mode IN ('daily', 'problem_solving')),
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
```

Please note: This table is already in the project Supabase

## Intended Usage Flow

1. **Create A/B Test**: Client calls `/api/ab_test/create` with user query and metadata
2. **Generate Variants**: System creates detailed and concise prompt versions
3. **Get Responses**: Both prompts are sent to LLM service with latency tracking
4. **Store Results**: All data saved to database with unique query_id
5. **User Selection**: Client presents both responses to user
6. **Submit Feedback**: User choice recorded via `/api/ab_test/feedback`

## Current Implementation Status

### Completed
- Basic API endpoints and models
- Prompt variant generation (detailed vs concise)
- Database schema and storage
- Latency measurement

### Incomplete
- **LLM Service Integration**: `call_llm_service()` is currently a placeholder (service.py:78-82)
- **Prompt Customization**: Enhance prompt generation for different interaction modes
- **Analytics Dashboard**: No data analysis or reporting features
- **Error Handling**: Limited error handling and validation
- **Testing**: No unit tests implemented
- **General Integration**: The current program flow does not yet use the ab_testing code and apis

## Future Development Notes

### Considerations
- The system currently hardcodes 'gpt-4' as the model (service.py:48)
- No rate limiting or quota management implemented
- Consider implementing experiment groups and statistical significance testing
- May need to add experiment configuration (test duration, sample size, etc.)