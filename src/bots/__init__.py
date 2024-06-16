from enum import Enum
from typing import Optional

from llama_index.core.storage import StorageContext

from src.bots.chat_bot import ChatBot
from src.bots.simple_openai_chat_bot import SimpleOpenAIChatBot
from src.db_handlers.schemas import RagBot


class BotType(str, Enum):
   SimpleOpenAIChatBot = 'SimpleOpenAIChatBot'


def create_chat_bot(
   bot: RagBot, storage_context: StorageContext, bot_type: Optional[BotType] = BotType.SimpleOpenAIChatBot
) -> ChatBot:
   if bot_type == BotType.SimpleOpenAIChatBot:
       return SimpleOpenAIChatBot.from_memory_obj(memory_obj=bot, storage_context=storage_context)
   else:
       raise NotImplementedError(f'Bot type {bot_type} not implemented')
  

