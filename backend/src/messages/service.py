from .CRUD import (
    create_message, get_messages, get_message,
    update_message, delete_message
)
from .models import MessageCreate, MessageUpdate

async def create_message_service(msg_data: MessageCreate):
    return await create_message(
        msg_data.message_id,
        msg_data.user_id,
        msg_data.content,
        msg_data.sender,
        msg_data.conversation_id
    )

async def get_messages_service(conversation_id):
    return await get_messages(conversation_id)

async def get_message_service(message_id):
    return await get_message(message_id)

async def update_message_service(message_id, msg_data: MessageUpdate):
    return await update_message(message_id, **msg_data.dict(exclude_unset=True))

async def delete_message_service(message_id):
    return await delete_message(message_id)