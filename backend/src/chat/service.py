import requests
import requests.exceptions
from ..logger import logger
from .models import ConversationCreate, ConversationUpdate, MessageCreate, MessageUpdate, MessageDelete, ChatRequest
from .CRUD import get_messages
import httpx
from typing import Optional, Dict, Any
import sys
import os

# Add the project root to the path so we can import config
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))
from config.constants import TimeoutConfig, ServiceConfig

BASE_URL = ServiceConfig.NEBULA_BASE_URL

def generate(data: ChatRequest) -> str:
    response = requests.post(f"{BASE_URL}/generate", data={"prompt": data.prompt, "reasoning": True})
    return response.json().get("result", "No result returned")

def generate_vision(prompt: str, image_path: str, fast: bool = False) -> str:
    with open(image_path, "rb") as img:
        files = {"file": img}
        data = {"prompt": prompt, "fast": str(fast).lower()}
        response = requests.post(f"{BASE_URL}/generate_vision", data=data, files=files)
    return response.json().get("result", "No result returned")

def nebula_text_endpoint(data: ChatRequest) -> str:
    """
    Sends a request to the API endpoint and returns the response with conversation context.

    Args:
        data: ChatRequest containing prompt and optional conversation_id

    Returns:
        str: The generated text from the API.
    """
    
    # Build conversation context if conversation_id is provided
    conversation_context = ""
    if data.conversation_id:
        try:
            messages = get_messages(data.conversation_id)
            
            if messages and len(messages) > 1:  # More than just the current message
                # Build conversation history (last 10 messages to avoid token limits)
                recent_messages = messages[-10:] if len(messages) > 10 else messages
                conversation_parts = []
                
                for msg in recent_messages[:-1]:  # Exclude the current message being processed
                    role = "User" if msg['sender'] == 'user' else "Assistant"
                    conversation_parts.append(f"{role}: {msg['content']}")
                
                if conversation_parts:
                    conversation_context = "\n".join(conversation_parts) + "\n\n"
        except Exception as e:
            print(f"Error loading conversation context: {e}")
    
    # Construct the full prompt with context
    if conversation_context:
        full_prompt = f"Previous conversation:\n{conversation_context}User: {data.prompt}\n\nAssistant:"
    else:
        full_prompt = f"User: {data.prompt}\n\nAssistant:"

    request_data = {
        "prompt": full_prompt,
        "reasoning": True,
    }
    
    try:
        response = requests.post(f"{BASE_URL}/generate", request_data, timeout=TimeoutConfig.CHAT_REQUEST_TIMEOUT)
        if response.status_code == 200:
            return response.json().get("result", "No result returned")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.ConnectTimeout:
        logger.error("Connection timeout to UWaterloo server")
        return "Sorry, the AI service is currently unavailable due to network timeout. Please try again later."
    except requests.exceptions.ConnectionError:
        logger.error("Connection error to UWaterloo server") 
        return "Sorry, the AI service is currently unavailable. Please check your internet connection."
    except Exception as e:
        logger.error(f"Request failed: {e}")
        return f"Error communicating with model: {str(e)}"

def open_ask(data: ConversationCreate):
    pass
    # course_id = -1
    # model_name = 'qwen'
    # system_prompt = None
    # # If a link is provided, try to match it to a course and retrieve its settings
    # if link is not None and len(link) > 0:
    #     course = db.query(Course).filter(Course.name == link).first()
    #     if course is not None:
    #         course_id = course.id
    #         model_name = course.model
    #         system_prompt = course.prompt

    # logger.info("Course ID: %s, Question: %s", course_id, data.message)

    # session_id = request.session.get("session_id")
    # conversation = []
    # print(session_id)
    # if session_id in cache:
    #     conversation = cache.get(session_id)
    # # conversation = request.session.get('conversation', [])
    # logger.info(conversation)

    # conversation.append({'question': question})
    # this_conversation = {'question': data.message}
    # # Limit the stored conversation length to prevent overly long context
    # MAX_CONVERSATION_LENGTH = 10
    # if len(conversation) > MAX_CONVERSATION_LENGTH:
    #     conversation = conversation[-MAX_CONVERSATION_LENGTH:]

    # SIMILARITY_THRESHOLD = 0.5
    # MAX_BACKGROUND_TOKENS = 500

    # background_query = "No documents uploaded, please provide background information."
    # background_summary = ""
    # summary = ""
    # # If course_id is valid, attempt to retrieve relevant context from DB
    # if course_id != -1:
    #     # collection_name = f"collection_{course_id}"
    #     # collection = collection_exists(collection_name)
    #     # if collection is not None:
    #     if conversation_exists(data.id):

    #         top_results_query = query_sentence_with_threshold(collection, question, 5, SIMILARITY_THRESHOLD)
    #         background_query = get_background_text(top_results_query, MAX_BACKGROUND_TOKENS)
    #         print(f"Background Query:\n{background_query}")

    #         if len(conversation) >= 1 and 'summary' in conversation[-1]:
    #             summary = conversation[-1]['summary']
    #             top_results_summary = query_sentence_with_threshold(collection, summary, 5, SIMILARITY_THRESHOLD)
    #             background_summary = get_background_text(top_results_summary, MAX_BACKGROUND_TOKENS)
    #             print(f"Background Summary:\n{background_summary}")

    # this_conversation['background'] = background_query + "\n" + background_summary

    # MAX_TOKENS = 1024
    # # Use a default system prompt if none is configured
    # if not system_prompt:
    #     system_prompt = ("Respond to the question using information in the "
    #                      "background. If no relevant information exists in the "
    #                      "background, you must say so and then refuse to "
    #                      "answer further.")

    # logger.info(question)
    # logger.info(system_prompt)
    # logger.info(background_query)
    # logger.info(summary)
    # logger.info('')
    # # Construct the final prompt including user query, background, and conversation summar
    # final_prompt = (
    #     f"You are a helpful teaching assistant.\n{system_prompt}\n\n"
    #     f"User Query:\n{question}\n\n"
    #     f"Based on this query, here is some background information that may be relevant (it may not be):\n{background_query}\n\n"
    #     f"This query is part of a longer conversation. Here is a brief summary:\n{summary}\n\n"
    #     f"Based on the summary, here is some additional background information that may be relevant (it may not be):\n{background_summary}\n\n"
    #     f"Please provide a response to the user's query."
    # )

    # # Generate an answer using the specified LLM
    # answer = text_text_eval(document_text=final_prompt, prompt_text=question, model=model_name, max_length=1024)

    # this_conversation['answer'] = answer
    # # Add the current Q&A to the conversation and update the summary
    # conversation.append(this_conversation)
    # new_summary = summarize_interaction(conversation)
    # conversation[-1]['summary'] = new_summary

    # logger.info(conversation)
    # # Store the updated conversation in cache
    # cache[session_id] = conversation
    # # Log the interaction to the database
    # entity = Log()
    # entity.create_time = datetime.now()
    # entity.background = background_query + "\n" + background_summary
    # entity.query = question
    # entity.answer = answer
    # entity.llm = answer
    # entity.link = link
    # entity.course_id = course_id
    # db.add(entity)
    # db.commit()

    # return {"answer": answer}

# manage context and tokens for conversation history
def build_conversation_history(conversation, max_tokens=1024):
    # Reconstruct conversation history from the end, ensuring token count does not exceed max_tokens
    conversation_history = ""
    total_tokens = 0
    for turn in reversed(conversation):
        user_turn = f"User: {turn['question']}\n"
        assistant_turn = f"Assistant: {turn.get('answer', '')}\n"
        turn_text = user_turn + assistant_turn
        turn_tokens = len(turn_text.split())
        if total_tokens + turn_tokens <= max_tokens:
            conversation_history = turn_text + conversation_history
            total_tokens += turn_tokens
        else:
            break
    return conversation_history

def get_background_text(background_chunks, max_background_tokens):
    # Concatenate background chunks up to a maximum token limit
    background_text = ""
    # total_tokens = 0
    # for chunk in background_chunks:
    #     chunk_tokens = len(tokenizer.tokenize(chunk))
    #     if total_tokens + chunk_tokens <= max_background_tokens:
    #         background_text += chunk + "\n"
    #         total_tokens += chunk_tokens
    #     else:
    #         break
    return background_text

def summarize_interaction(conversation, max_tokens=150):
    # Summarize the last user-assistant exchange.
    last_exchange = f"User: {conversation[-1]['question']}\nAssistant: {conversation[-1]['answer']}\n"

    previous_summary = conversation[-2]['summary'] if len(conversation) > 1 and 'summary' in conversation[-2] else ''

    summary_prompt = f"Previous Summary:\n{previous_summary}\n\nNew Interaction:\n{last_exchange}\n\nUpdate the summary, keeping it under {max_tokens} tokens."

    # Generate a summary of the updated conversation
    # summary = text_text_eval(document_text="", prompt_text=summary_prompt, model="qwen", max_length=max_tokens)
    summary = nebula_text_endpoint(ChatRequest(prompt=summary_prompt))
    return summary.strip()

# replaced text_text_eval with just the stable nebula endpoint we have at the top since it just redirects based on model name

async def get_most_recent_user_query(conversation_id: str) -> Optional[str]:
    """
    Get the most recent user query from the messages table.
    Returns the content of the last user message in the conversation.
    """
    try:
        messages = get_messages(conversation_id)
        
        # Filter for user messages and get the most recent one
        user_messages = [msg for msg in messages if msg.get('sender') == 'user']
        
        if user_messages:
            # Messages are ordered by created_at, so take the last one
            most_recent = user_messages[-1]
            return most_recent.get('content', '')
        
        return None
    except Exception as e:
        print(f"Error getting recent user query: {e}")
        return None

async def query_rag_system(conversation_id: str, question: str) -> Optional[Dict[str, Any]]:
    """
    Query the RAG system for relevant information based on the user's question.
    """
    try:
        async with httpx.AsyncClient(timeout=TimeoutConfig.RAG_QUERY_TIMEOUT) as client:
            rag_payload = {
                'course_id': conversation_id,  # Using conversation_id as course_id
                'question': question
            }
            
            response = await client.post(
                f'http://{ServiceConfig.LOCALHOST}:{ServiceConfig.RAG_SYSTEM_PORT}/ask',
                json=rag_payload
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"RAG system returned {response.status_code}: {response.text}")
                return None
    
    except Exception as e:
        print(f"Error querying RAG system: {e}")
        return None

def enhance_prompt_with_rag_context(original_prompt: str, rag_result: Optional[Dict[str, Any]]) -> str:
    """
    Enhance the original prompt with context from RAG system if available.
    """
    if not rag_result or not rag_result.get('success'):
        return original_prompt
    
    answer = rag_result.get('answer', '')
    sources = rag_result.get('sources', [])
    
    # Build context from actual document content
    document_context = ""
    if sources:
        document_context = "Relevant document content:\n\n"
        for i, source in enumerate(sources, 1):
            content = source.get('content', '')
            score = source.get('score', 0)
            # Convert score to float if it's a string
            try:
                score_float = float(score)
            except (ValueError, TypeError):
                score_float = 0.0
            document_context += f"Document {i} (relevance: {score_float:.3f}):\n{content}\n\n"
    
    # Create enhanced prompt with actual document content
    enhanced_prompt = f"""You have access to relevant information from uploaded documents. Use this context to answer the user's question.

{document_context}

User question: {original_prompt}

Please provide a comprehensive answer based on the document content above. Reference specific information from the documents when relevant."""
    
    return enhanced_prompt
