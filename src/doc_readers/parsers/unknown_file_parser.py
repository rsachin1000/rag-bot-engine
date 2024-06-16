from typing import Any, List, Optional, Sequence


from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.node_parser.interface import NodeParser
from llama_index.core.schema import BaseNode
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Document


from src.logger import CustomLogger


logger = CustomLogger(name=__name__)


class UnknownFileTypeParser(NodeParser):
   """Simple file node parser."""
   @classmethod
   def from_defaults(
       cls,
       include_metadata: bool = True,
       include_prev_next_rel: bool = True,
       callback_manager: Optional[CallbackManager] = None,
   ) -> "UnknownFileTypeParser":
       callback_manager = callback_manager or CallbackManager([])


       return cls(
           include_metadata=include_metadata,
           include_prev_next_rel=include_prev_next_rel,
           callback_manager=callback_manager,
       )

   @classmethod
   def class_name(cls) -> str:
       """Get class name."""
       return "UnknownFileTypeParser"

   def get_nodes_from_documents(
           self,
           documents: Sequence[Document],
           show_progress: bool = False,
           **kwargs: Any,
       ) -> List[BaseNode]:
       """Parse documents into nodes.
       """
       parser=SentenceSplitter()
       nodes=  parser.get_nodes_from_documents(documents=documents, show_progress=show_progress, **kwargs)
      
       if len(nodes)/len(documents) > 10: #TODO: do something for this situation
           logger.warning("Too many nodes per document. ={len(nodes)/len(documents)}")
          
       return nodes
  
   def _parse_nodes(
       self, nodes: Sequence[BaseNode], show_progress: bool = False, **kwargs: Any
   ) -> List[BaseNode]:
       raise NotImplementedError("Not implemented yet")

