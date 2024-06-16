from typing import List, Dict


from llama_index.core import Document
from llama_index.core.schema import BaseNode
from llama_index.core.node_parser.interface import NodeParser


from src.logger import CustomLogger
from src.doc_readers.parsers.ipynb_file_parser import JupyterNotebookParser
from src.doc_readers.parsers.md_file_parser import MarkdownParser
from src.doc_readers.parsers.unknown_file_parser import UnknownFileTypeParser


logger = CustomLogger(name=__name__)


parsers_dict: Dict[str, NodeParser] = {
   ".md": MarkdownParser(),
   ".ipynb": JupyterNotebookParser(),
   # Additional parsers can be added here
   'default': UnknownFileTypeParser(),
}


class Parser:
   @staticmethod
   def parse_documents(documents: List[Document]) -> List[BaseNode]:
       grouped_documents = {}
       for document in documents:
           extension = '.' + document.metadata['file_name'].split('.')[-1]
           if extension in parsers_dict:
               if extension not in grouped_documents:
                   grouped_documents[extension] = []
               grouped_documents[extension].append(document)
           else:
               logger.info(f"No parser available for extension {extension}, default is used.")
               if 'default' not in grouped_documents:
                   grouped_documents['default'] = []
               grouped_documents['default'].append(document)
      
       results = []
       for extension, docs in grouped_documents.items():
           parser = parsers_dict.get(extension)
           if parser:
               nodes = parser.get_nodes_from_documents(docs, show_progress=True)
               results.extend(nodes)
           else:
               logger.error(f"Something went wrong with {extension}")
       return results
