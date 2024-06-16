from typing import List, Optional
from pydantic import BaseModel, Field

from llama_index.core.chat_engine.types import AgentChatResponse

from src.db_handlers.schemas import CrawlResource, RagBot, SourceNodeWithScore, User
from src.db_handlers.schemas import BotIndex


class HealthCheckResponse(BaseModel):
   status: str


class CreateChatBotOutput(BaseModel):
   bot_id: str
   name: str
   def __init__(self, rag_bot: RagBot):
       super().__init__(bot_id=rag_bot.bot_id, name=rag_bot.name)
  
  
class ChatBotOutput(BaseModel):
   bot_id: str
   name: str
   description: str
   llm_model_name: str
   embeddings_model_name: str
   user: User
   created_at: str
   updated_at: str
   crawl_resources: List[CrawlResource]
   indexes: List[BotIndex]
   ready: bool
   def __init__(self, rag_bot: RagBot):
       super().__init__(
           bot_id=rag_bot.bot_id,
           name=rag_bot.name,
           description=rag_bot.description,
           llm_model_name=rag_bot.llm_model,
           embeddings_model_name=rag_bot.embeddings_model,
           user=rag_bot.user,
           created_at=rag_bot.created_at,
           updated_at=rag_bot.updated_at,
           crawl_resources=rag_bot.crawl_resources,
           indexes=rag_bot.indexes,
           ready=rag_bot.ready
       )


class BotNameUpdateResponse(BaseModel):
   status: bool
   message: Optional[str] = None


class BotDescUpdateResponse(BaseModel):
   status: bool
   message: Optional[str] = None


class GetChatSessionIdResponse(BaseModel):
   chat_session_id: str


class InsertChatSessionFeedbackResponse(BaseModel):
   status: bool


class InsertChatMessageFeedbackResponse(BaseModel):
   status: bool


class ChatRequest(BaseModel):
   query: str
  

class ChatResponse(BaseModel):
   response: str
   resources: List[str] = Field(
       default_factory=list,
       description="List of URLs of the resources used to generate the response",
   )

   @classmethod
   def from_agent_response(cls, response: AgentChatResponse):
       resources_list = [
           sn.metadata["url"] for sn in response.source_nodes
       ]
       resources_list = list(set(resources_list))
       return cls(response=response.response, resources=resources_list)

