from typing import List, Optional

from llama_index.core.base.llms.types import ChatMessage, MessageRole

from src.db_handlers.schemas import Message, MessageCreatorRole


def convert_db_messages_to_chatbot_messages(
    db_messages: Optional[List[Message]]
) -> Optional[List[ChatMessage]]:
    if db_messages is None:
        return None

    chatbot_messages = []
    for db_message in db_messages:
        role = None
        if db_message.role == MessageCreatorRole.USER:
            role = MessageRole.USER
        elif db_message.role == MessageCreatorRole.ASSISTANT:
            role = MessageRole.ASSISTANT
        else:
            raise ValueError(f"Unknown role {db_message.role}")
        
        chatbot_message = ChatMessage(
            content=db_message.text,
            role=role,
        )
        chatbot_messages.append(chatbot_message)

    return chatbot_messages
