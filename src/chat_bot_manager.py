import asyncio
import json
from typing import List, Optional, Tuple, Set


import chromadb
from chromadb.api.models.Collection import Collection
from starlette.responses import ContentStream
from llama_index.core.storage import StorageContext
from llama_index.storage.docstore.mongodb import MongoDocumentStore
from llama_index.storage.index_store.mongodb import MongoIndexStore
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.chat_engine.types import StreamingAgentChatResponse
from llama_index.core.vector_stores.types import BasePydanticVectorStore
from llama_index.core.storage.docstore.keyval_docstore import KVDocumentStore
from llama_index.core.storage.index_store.keyval_index_store import KVIndexStore


from src import config
from src.config_constants import MONGO_DB, CHROMA_DB
from src.db_handlers import get_db_handler, DBHandler
from src.bots import create_chat_bot, ChatBot
from src.logger import CustomLogger
from src.db_handlers.schemas import (
   RagBot, BotConfig, Message, ChatSession, User, MessageCreatorRole, SourceNodeWithScore
)
from src.utils import convert_db_messages_to_chatbot_messages


logger = CustomLogger(__name__)


class ChatBotManager:
   def __init__(self):
       self._storage_context: StorageContext = self._get_storage_context()
       self._db_handler: DBHandler = get_db_handler(db_type=config.app_cfg.DbStore)
      
   def _get_storage_context(self) -> StorageContext:
       docstore = self._get_doc_store()
       index_store = self._get_index_store()
       vector_store = self._get_vector_store()
      
       return StorageContext.from_defaults(
           docstore=docstore,
           index_store=index_store,
           vector_store=vector_store,
       )
  
   def _get_vector_store(self) -> BasePydanticVectorStore:
       vector_store = None
       if config.llama_index_cfg.VectorStoreType == CHROMA_DB:
           chroma_client = chromadb.PersistentClient()
           chroma_collection: Collection = chroma_client.get_or_create_collection(
               name=config.llama_index_cfg.VectorStore.CollectionName
           )
           vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
       else:
           raise NotImplementedError(
               f"VectorStoreType: {config.llama_index_cfg.VectorStoreType} not implemented"
           )
       return vector_store
  
   def _get_doc_store(self) -> KVDocumentStore:
       docstore = None
       if config.llama_index_cfg.DocStoreType == MONGO_DB:
           docstore = MongoDocumentStore.from_uri(uri=config.llama_index_cfg.MongoURI)
       else:
           raise NotImplementedError(
               f"DocStoreType: {config.llama_index_cfg.DocStoreType} not implemented"
           )
       return docstore
  
   def _get_index_store(self) -> KVIndexStore:
       index_store = None
       if config.llama_index_cfg.DocStoreType == MONGO_DB:
           index_store = MongoIndexStore.from_uri(uri=config.llama_index_cfg.MongoURI)
       else:
           raise NotImplementedError(
               f"IndexStoreType: {config.llama_index_cfg.DocStoreType} not implemented"
           )
       return index_store
  
   async def acreate_bot(self, bot: RagBot, chat_history: Optional[List[Message]] = None) -> ChatBot:#
       chat_bot: ChatBot = create_chat_bot(bot=bot, storage_context=self._storage_context)
       indexes_loaded = await chat_bot.acreate_or_load_indexes()
      
       if not indexes_loaded:
           logger.error(
               message="Failed to load indexes for bot",
               fields={
                   "bot_id": bot.bot_id,
                   "bot_name": bot.name,
               }
           )
           return chat_bot


       bot_chat_history = convert_db_messages_to_chatbot_messages(chat_history)
       chat_bot.create_super_agent(chat_history=bot_chat_history, verbose=True)
      
       if not bot.indexes:
           self._db_handler.update_bot_indexes(
               bot_id=bot.bot_id,
               resource_to_index_map=chat_bot.get_resources_to_index_map()
           )
      
       if not bot.ready:
           self._db_handler.update_bot_status(bot_id=bot.bot_id, status=True)
      
       return chat_bot
  
   async def create_new_bot(self, bot_config: BotConfig) -> RagBot:
       bot_memory_obj = RagBot.from_config(config=bot_config)
       self._db_handler.create_bot(bot_memory_obj)
       asyncio.create_task(self.acreate_bot(bot=bot_memory_obj))
       return bot_memory_obj
  
   async def _chat(
       self, user_query: str, bot_id: str, chat_session_id: str, user: User
   ) -> Tuple[RagBot, ChatSession]:
       bot_memory_obj = self._db_handler.get_bot(bot_id)
       if bot_memory_obj is None:
           return "Bot with id: `{bot_id}` not found"
      
       if not bot_memory_obj.ready:
           return "Bot is not ready yet to answer queries. Please try again later."
      
       chat_session: ChatSession = self._db_handler.get_chat_session(
           chat_session_id=chat_session_id
       )
      
       if chat_session is None:
           logger.info(
               message="Chat session does not exist. Creating a new one.",
               fields={
                   "chat_session_id": chat_session_id,
                   "bot_id": bot_id,
               }
           )
           chat_session: ChatSession = self._db_handler.create_session(
               bot_id=bot_id,
               chat_session_id=chat_session_id,
               chat_session_name=user_query[:20],
               user=user,
           )
      
       self._db_handler.create_message(
           chat_session_id=chat_session_id,
           text=user_query,
           role=MessageCreatorRole.USER,
       )
      
       chat_session.messages.append(
           Message.from_role(
               text=user_query,
               role=MessageCreatorRole.USER
           )
       )
       return bot_memory_obj, chat_session
  
   async def chat(
       self, user_query: str, bot_id: str, chat_session_id: str, user: User,
   ) -> str:
       bot_memory_obj, chat_session = await self._chat(
           user_query, bot_id, chat_session_id, user
       )
       chat_bot = await self.acreate_bot(bot=bot_memory_obj, chat_history=chat_session.messages)
       response = chat_bot.chat(user_query=user_query)
      
       source_nodes = [
           SourceNodeWithScore(
               node_id=sn.node_id,
               url=sn.metadata["url"],
               score=sn.score
           )
           for sn in response.source_nodes
       ]
      
       self._db_handler.create_message(
           chat_session_id=chat_session_id,
           text=response.response,
           role=MessageCreatorRole.ASSISTANT,
           sources_nodes=source_nodes,
       )
       return response

   async def stream_chat(
       self, user_query: str, bot_id: str, chat_session_id: str, user: User,
   ) -> ContentStream:
       bot_memory_obj, chat_session = await self._chat(
           user_query, bot_id, chat_session_id, user
       )
       chat_bot = await self.acreate_bot(bot=bot_memory_obj, chat_history=chat_session.messages)
       response = chat_bot.chat_stream(user_query=user_query)
      
       return self.stream_generator(response=response, chat_session_id=chat_session_id)
  
   async def stream_generator(self, response: StreamingAgentChatResponse, chat_session_id: str):
       token_array: List[str] = []
      
       resources_list: List[SourceNodeWithScore] = [
           SourceNodeWithScore(
               node_id=sn.node_id,
               url=sn.metadata["url"],
               score=sn.score
           )
           for sn in response.source_nodes
       ]
      
       resources_set: Set[str] = set()
       for resource in resources_list:
           resources_set.add(resource.url)
      
       # Yield Sources
       sources_json = json.dumps({'resources': list(resources_set)})
       yield f"data: {sources_json}\n\n"
      
       for token in response.response_gen:
           token_array.append(token)
           yield f"data: {token}\n\n"
      
       assistant_response = "".join(token_array)
       self._db_handler.create_message(
           chat_session_id=chat_session_id,
           text=assistant_response,
           role=MessageCreatorRole.ASSISTANT,
           sources_nodes=resources_list,
       )
