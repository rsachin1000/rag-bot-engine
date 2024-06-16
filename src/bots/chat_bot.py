from abc import ABC, abstractmethod
from typing import Optional, Dict, List

from llama_index.core.llms.llm import LLM
from llama_index.core.agent.runner.base import AgentRunner
from llama_index.core.base.embeddings.base import BaseEmbedding
from llama_index.core.storage import StorageContext
from llama_index.core.indices import VectorStoreIndex
from llama_index.core.chat_engine.types import (
   AgentChatResponse,
   StreamingAgentChatResponse
)
from llama_index.core.base.llms.types import ChatMessage

from src.db_handlers.schemas import CrawlResource, RagBot, GithubRepoResource, BotIndex


class ChatBot(ABC):
   def __init__(
       self,
       bot_id: str,
       name: str,
       description: str,
       llm: LLM,
       embeddings_model: BaseEmbedding,
       storage_context: StorageContext,
       indexes: List[BotIndex],
       crawl_resources: List[CrawlResource],
   ) -> None:
       self.bot_id = bot_id
       self._name = name
       self._description = description
       self._llm = llm
       self._storage_context = storage_context
       self._embeddings_model = embeddings_model
       self._resource_to_index_map: Dict[str, str] = {
           idx.resource: idx.index_id for idx in indexes
       }
       self._indexes: List[VectorStoreIndex] = []
      
       self.crawl_resources = crawl_resources
      
       self.super_agent: Optional[AgentRunner] = None
      
   @classmethod
   @abstractmethod
   def from_memory_obj(cls, memory_obj: RagBot) -> "ChatBot":
       raise NotImplementedError
  
   @abstractmethod
   def chat(self, user_query: str) -> AgentChatResponse:
       raise NotImplementedError
  
   @abstractmethod
   def chat_stream(self, user_query: str) -> StreamingAgentChatResponse:
       raise NotImplementedError
  
   @abstractmethod
   async def acreate_or_load_indexes(self) -> bool:
       raise NotImplementedError
  
   @abstractmethod
   def create_super_agent(
       self, chat_history: Optional[List[ChatMessage]] = None, verbose: bool = False
   ) -> None:
       raise NotImplementedError
  
   def get_resources_to_index_map(self) -> Dict[str, str]:
       return self._resource_to_index_map
  
