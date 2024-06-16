from typing import Dict
from llama_index.core.node_parser.interface import NodeParser
from src.doc_readers.parsers.ipynb_file_parser import JupyterNotebookParser
from src.doc_readers.parsers.md_file_parser import MarkdownParser
from src.doc_readers.parsers.unknown_file_parser import UnknownFileTypeParser


_parsers: Dict[str, NodeParser] = {
   ".md": MarkdownParser(),
   ".ipynb": JupyterNotebookParser(),
   # Additional parsers can be added here
   'default': UnknownFileTypeParser(),
}


def get_all_parsers() -> Dict[str, NodeParser]:
   """Return all parser instances as a dictionary."""
   return _parsers
