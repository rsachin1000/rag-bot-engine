from typing import Any, List, Optional, Sequence
from llama_index.core.callbacks.base import CallbackManager
from llama_index.core.schema import BaseNode
from llama_index.core.node_parser.file.markdown import MarkdownNodeParser
from llama_index.core import Document


class MarkdownParser(MarkdownNodeParser):
   @classmethod
   def from_defaults(
       cls,
       include_metadata: bool = True,
       include_prev_next_rel: bool = True,
       callback_manager: Optional[CallbackManager] = None,
   ) -> "MarkdownParser":
       callback_manager = callback_manager or CallbackManager([])
       return cls(
           include_metadata=include_metadata,
           include_prev_next_rel=include_prev_next_rel,
           callback_manager=callback_manager,
       )
  
   @classmethod
   def class_name(cls) -> str:
       return "MarkdownParser"
  
   def get_nodes_from_documents(
           self,
           documents: Sequence[Document],
           show_progress: bool = False,
           **kwargs: Any,
       ) -> List[BaseNode]:
      
       nodes=super().get_nodes_from_documents(documents=documents,
               show_progress=show_progress, **kwargs)
       return nodes
  
