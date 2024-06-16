from typing import List, Optional


from llama_index.llms.openai import OpenAI
from llama_index.agent.openai import OpenAIAgent
from llama_index.core.storage import StorageContext
from llama_index.core.base.llms.types import ChatMessage
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.chat_engine.types import (
   AgentChatResponse,
   StreamingAgentChatResponse,
)
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from llama_index.core.vector_stores import FilterOperator, FilterCondition
from llama_index.core.indices import load_index_from_storage, VectorStoreIndex

from src.db_handlers.schemas import ConfluenceResource, CrawlResource, RagBot, GithubRepoResource, BotIndex, WebResource
from src.bots.chat_bot import ChatBot
from src.doc_readers.confluence_reader.confluence_reader import ConfluencePageReader
from src.doc_readers.github_reader.github_reader import GithubReader
from src.doc_readers.web_page_reader import WebPageReader
from src.logger import CustomLogger
from src.tools import StandardRetrieverQueryEngineTool
from src.bots.utils import create_unique_id


logger = CustomLogger(__name__)


"""
TODO: We can add `SYSTEM_PROMPT` to the super agent to improve performance.
"""


DOC_INDEX_ID_METADATA_KEY = "index_id"


class SimpleOpenAIChatBot(ChatBot):
   def __init__(
       self,
       bot_id: str,
       name: str,
       description: str,
       llm_model_name: str,
       embeddings_model_name: str,
       storage_context: StorageContext,
       indexes: List[BotIndex] = [],
       crawl_resources: List[CrawlResource] = []
   ) -> None:
       super().__init__(
           bot_id=bot_id,
           name=name,
           description=description,
           llm= OpenAI(model=llm_model_name),
           embeddings_model= OpenAIEmbedding(model=embeddings_model_name),
           storage_context=storage_context,
           indexes=indexes,
           crawl_resources=crawl_resources,
       )
  
   @classmethod
   def from_memory_obj(self, memory_obj: RagBot, storage_context: StorageContext) -> "SimpleOpenAIChatBot":
       return SimpleOpenAIChatBot(
           bot_id=memory_obj.bot_id,
           name=memory_obj.name,
           description=memory_obj.description,
           llm_model_name=memory_obj.llm_model,
           embeddings_model_name=memory_obj.embeddings_model,
           storage_context=storage_context,
           indexes=memory_obj.indexes,
           crawl_resources=memory_obj.crawl_resources,
       )
  
   async def acreate_or_load_indexes(self) -> bool:
       logger.info(message="indexing started", fields={"bot_id": self.bot_id})
       if not self._resource_to_index_map:
           github_reader = GithubReader()
           confluence_page_reader = ConfluencePageReader()
           web_page_reader = WebPageReader()
          
           for resource in self.crawl_resources:
               _index_id = create_unique_id()
               documents=None
               nodes=None
               if isinstance(resource, GithubRepoResource):
                   documents = await github_reader.read_documents(
                       resource=resource, chatbot_id=self.bot_id, verbose=False
                   )
                  
                   # set index_id metadata field for each document
                   for doc in documents:
                       doc.metadata[DOC_INDEX_ID_METADATA_KEY] = _index_id
                  
                   nodes = github_reader.parse_documents(documents=documents)
                   logger.info(
                       message="read and parse documents from github",
                       fields={"bot_id": self.bot_id},
                   )
               elif isinstance(resource, ConfluenceResource):
                   documents = confluence_page_reader.read_documents(resource=resource, chatbot_id=self.bot_id, verbose=False)
                  
                   # set index_id metadata field for each document
                   for doc in documents:
                       doc.metadata[DOC_INDEX_ID_METADATA_KEY] = _index_id
                  
                   nodes = confluence_page_reader.parse_documents(documents=documents)
                   logger.info(
                       message="read and parse documents from confluence",
                       fields={"bot_id": self.bot_id},
                   )
               elif isinstance(resource, WebResource):
                   documents = web_page_reader.read_documents(resource=resource, chatbot_id=self.bot_id, verbose=False)
                  
                   # set index_id metadata field for each document
                   for doc in documents:
                       doc.metadata[DOC_INDEX_ID_METADATA_KEY] = _index_id
                  
                   nodes=web_page_reader.parse_documents(documents=documents)
                   logger.info(
                       message="read and parse documents from web",
                       fields={"bot_id": self.bot_id},
                   )
               else:
                   logger.error(
                       message="Invalid resource type",
                       fields={"bot_id": self.bot_id, "resource": resource}
                   )
                   continue
              
               for doc in documents:
                   self._storage_context.docstore.set_document_hash(doc.get_doc_id(), doc.hash)
              
               logger.info(
                   message="stored document hashes in docstore",
                   fields={"bot_id": self.bot_id},
               )
              
               logger.info(message="creating a new index")
               index = VectorStoreIndex(
                   nodes=nodes,
                   storage_context=self._storage_context,
                   embed_model=self._embeddings_model,
                   show_progress=True,
               )
               index.set_index_id(_index_id)
              
               logger.info(
                   message="Created a new index",
                   fields={
                       "bot_id": self.bot_id,
                       "index_id": index.index_id,
                       "resource_url": resource.url
                   }
               )
              
               # add the new index to the list of indexes
               self._resource_to_index_map[resource.url] = index.index_id
               self._indexes.append(index)
              
               # persist the index
           self._storage_context.persist()
           logger.info(
               message='persisted indexes to storage',
               fields={"bot_id": self.bot_id},
           )
       else:
           for url, index_id in self._resource_to_index_map.items():
               index = load_index_from_storage(storage_context=self._storage_context, index_id=index_id)
               self._indexes.append(index)
               logger.info(
                   message="Loaded index from storage",
                   fields={
                       "bot_id": self.bot_id,
                       "index_id": index_id,
                       "resource_url": url
                   }
               )
      
       return True
              
   def create_super_agent(
       self, chat_history: Optional[List[ChatMessage]] = None, verbose: bool = False
   ):
       tools_list = []
       for index in self._indexes:
           filters = MetadataFilters(
               filters=[
                   MetadataFilter(
                       key=DOC_INDEX_ID_METADATA_KEY,
                       value=index.index_id,
                       operator=FilterOperator.EQ
                   ),
               ],
               condition=FilterCondition.AND,
           )
           tool = StandardRetrieverQueryEngineTool.from_defaults(
               index=index,
               llm=self._llm,
               filters=filters,
           )
           tools_list.append(tool)
      
       self.super_agent = OpenAIAgent.from_tools(
           tools=tools_list,
           llm=self._llm,
           chat_history=chat_history,
           verbose=verbose,
       )
       if self.super_agent:
           logger.info(
               message="Super agent created",
               fields={"bot_id": self.bot_id}
           )
       else:
           logger.error(
               message="Failed to create super agent",
               fields={"bot_id": self.bot_id}
           )
  
   def chat(self, user_query: str) -> AgentChatResponse:
       return self.super_agent.chat(user_query)
  
   def chat_stream(self, user_query: str) -> StreamingAgentChatResponse:
       return self.super_agent.stream_chat(user_query)
