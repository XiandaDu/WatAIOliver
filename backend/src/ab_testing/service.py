from ..supabaseClient import supabase
from .prompt_generator import PromptGenerator
from .models import ABTestFeedback
from uuid import uuid4, UUID
import time
from typing import Tuple, Dict, Any

async def create_ab_test_query(
    user_query: str, 
    user_id: UUID, 
    course_id: UUID, 
    interaction_mode: str
) -> Dict[str, Any]:
    """Create A/B test with two prompt variants"""

    query_id = uuid4()
    generator = PromptGenerator()

    # Generate prompt variants based on interaction mode
    prompt_a, prompt_b = generator.generate_variants(
        user_query,
        interaction_mode=interaction_mode
    )

    # Generate responses
    start_time = time.time()
    response_a = await call_llm_service(prompt_a)
    latency_a = int((time.time() - start_time) * 1000)

    start_time = time.time()
    response_b = await call_llm_service(prompt_b)
    latency_b = int((time.time() - start_time) * 1000)

    # Store in database
    ab_test_data = {
        'query_id': str(query_id),
        'user_id': str(user_id),
        'course_id': str(course_id) if course_id else None,
        'interaction_mode': interaction_mode,
        'original_query': user_query,
        'prompt_variant_a': prompt_a,
        'prompt_variant_b': prompt_b,
        'response_a': response_a,
        'response_b': response_b,
        'latency_a': latency_a,
        'latency_b': latency_b,
        #Note: Replace with actual model
        'model_used': 'gpt-4' 
    }

    result = supabase.table('ab_test_logs').insert(ab_test_data).execute()

    return {
        'query_id': query_id,
        'response_a': response_a,
        'response_b': response_b,
        'metadata': {
            'latency_a': latency_a,
            'latency_b': latency_b
        }
    }

async def submit_ab_test_feedback(feedback: ABTestFeedback) -> bool:
    """Submit user's choice and feedback"""

    update_data = {
        'chosen_response_id': feedback.chosen_response_id,
        'feedback_text': feedback.feedback_text,
        'feedback_submitted_at': 'now()'
    }

    result = supabase.table('ab_test_logs').update(update_data).eq(
        'query_id', str(feedback.query_id)
    ).execute()

    return len(result.data) > 0

async def call_llm_service(prompt: str) -> str:
    """Replace this with actual LLM service call"""
    # This should call existing LLM service
    # For now, returning placeholder
    return f"Response to: {prompt[:50]}..."