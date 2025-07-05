from .CRUD import (
    create_message, get_messages, get_message,
    update_message, delete_message
)
from .models import MessageCreate, MessageUpdate

def create_message_service(msg_data: MessageCreate):
    return create_message(
        msg_data.message_id,
        msg_data.user_id,
        msg_data.content,
        msg_data.sender,
        msg_data.conversation_id
    )

def get_messages_service(conversation_id):
    return get_messages(conversation_id)

def get_message_service(message_id):
    return get_message(message_id)

def update_message_service(message_id, msg_data: MessageUpdate):
    return update_message(message_id, **msg_data.dict(exclude_unset=True))

def delete_message_service(message_id):
    return delete_message(message_id)