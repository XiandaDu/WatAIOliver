import requests
from ..logger import logger
from .models import ConversationCreate, ConversationUpdate, MessageCreate, MessageUpdate, MessageDelete

BASE_URL = "http://ece-nebula07.eng.uwaterloo.ca:8976"  # This is the stable endpoint

def generate(data: ConversationUpdate) -> str:
    response = requests.post(f"{BASE_URL}/generate", data={"prompt": data.message, "reasoning": data.reasoning})
    return response.json().get("result", "No result returned")

def generate_vision(prompt: str, image_path: str, fast: bool = False) -> str:
    with open(image_path, "rb") as img:
        files = {"file": img}
        data = {"prompt": prompt, "fast": str(fast).lower()}
        response = requests.post(f"{BASE_URL}/generate_vision", data=data, files=files)
    return response.json().get("result", "No result returned")

def nebula_text_endpoint(data: ConversationUpdate) -> str:
    """
    Sends a request to the API endpoint and returns the response.

    Args:
        document_path (str): Path to the document.
        prompt_text (str): The prompt text to be used for processing.

    Returns:
        str: The generated text from the API.
    """

    data = {
        "prompt": f"{data.message}",
        "reasoning": True,
    }
    
    response = requests.post(f"{BASE_URL}/generate", data)
    return response.json().get("result", "No result returned")

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
    summary = nebula_text_endpoint(ConversationUpdate(message=summary_prompt, reasoning=False))
    return summary.strip()

# replaced text_text_eval with just the stable nebula endpoint we have at the top since it just redirects based on model name
