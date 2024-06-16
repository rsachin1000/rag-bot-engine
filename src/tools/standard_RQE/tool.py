from typing import Optional, List
from pydantic import BaseModel


from llama_index.core.llms.llm import LLM
from llama_index.core.indices.base import BaseIndex
from llama_index.core.tools import QueryEngineTool
from llama_index.core.response_synthesizers import (
   BaseSynthesizer,
   ResponseMode,
   get_response_synthesizer,
)
from llama_index.core.settings import Settings, callback_manager_from_settings_or_context
from llama_index.core.base.base_retriever import BaseRetriever
from llama_index.core.service_context import ServiceContext
from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.vector_stores import MetadataFilters
from llama_index.core.query_engine.retriever_query_engine import RetrieverQueryEngine


from src.tools.base_tool import BaseTool


class StandardRetrieverQueryEngineTool(BaseTool):
  
   @classmethod
   def from_defaults(
       cls,
       index: BaseIndex,
       llm: LLM,
       name: str = None,
       description: str = None,
       streaming: bool = False,
       response_mode: ResponseMode = ResponseMode.COMPACT,
       filters: Optional[MetadataFilters] = None,
       service_context: Optional[ServiceContext] = None,
       output_cls: Optional[BaseModel] = None,
       verbose: bool = False,
   ) -> QueryEngineTool:
       retriever: BaseRetriever = index.as_retriever(filters=filters)
      
       callback_manager = callback_manager_from_settings_or_context(
           Settings, service_context
       )
      
       synthesizer: BaseSynthesizer = get_response_synthesizer(
           llm=llm,
           response_mode=response_mode,
           streaming=streaming,
           callback_manager=callback_manager,
           output_cls=output_cls,
           verbose=verbose,
       )
      
       node_postprocessors: Optional[List[BaseNodePostprocessor]] = []

       query_engine = RetrieverQueryEngine(
           retriever=retriever,
           response_synthesizer=synthesizer,
           node_postprocessors=node_postprocessors,
           callback_manager=callback_manager,
       )
      
       return QueryEngineTool.from_defaults(
           query_engine=query_engine,
           name=name,
           description=description,
       )
      
      
      

