from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Dict, List
import fnmatch

from llama_index.core.schema import BaseNode
from llama_index.core import Document

from src.db_handlers.schemas import CrawlResource
from src.doc_readers.parsers import get_all_parsers
from src.logger import CustomLogger


logger = CustomLogger(__name__)


class DocReader(ABC):
   @abstractmethod
   def read_documents(self, resources: CrawlResource, verbose: bool = False) -> List[Document]:
       """Reads and parses the resources.
       Args:
           resources (List[CrawlResource]): list of resources to read and parse

       Returns:
           List[Node]: list of nodes
       """
       raise NotImplementedError
  
   def parse_documents(self, documents: List[Document], verbose: bool = False) -> List[BaseNode]:
       grouped_documents: Dict[str, List[Document]] = defaultdict(list)
       parsers_dict = get_all_parsers()
       for document in documents:
           file_name: str = document.metadata['url'] #TODO check this
           extension = '.' + file_name.split('.')[-1]
           if extension in parsers_dict:
               grouped_documents[extension].append(document)
           else:
               logger.warning(f"No parser available for extension {extension}, default is used.")
               grouped_documents['default'].append(document)
      
       results: List[BaseNode] = []
       for extension, docs in grouped_documents.items():
           parser = parsers_dict.get(extension)
           if parser:
               nodes = parser.get_nodes_from_documents(docs, show_progress=True)
               results.extend(nodes)
           else:
               logger.error(f"Something went wrong with {extension}")
       return results
  
   def _ignore_files_matching_pattern(self, urls, patterns, base_path=None):
       filtered_urls = []
       for url in urls:
           if base_path:
               if url.startswith(base_path):
                   path = url[len(base_path):]
               else:
                   continue
           else:
               path=url
           if not any(fnmatch.fnmatch(path, pattern) for pattern in patterns):
               filtered_urls.append(url)
       return filtered_urls
  
   def _include_files_matching_pattern(self, urls, patterns, base_path=None):
       filtered_urls = []
       for url in urls:
           if base_path:
               if url.startswith(base_path):
                   path = url[len(base_path):]
               else:
                   continue
           else:
               path=url
           if any(fnmatch.fnmatch(path, pattern) for pattern in patterns):
               filtered_urls.append(url)
       return filtered_urls
