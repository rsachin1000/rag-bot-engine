import re
from typing import List

from llama_index.core import Document

from llama_index.readers.confluence.base import ConfluenceReader

from src.db_handlers.schemas import ConfluenceResource
from src.doc_readers.doc_reader import DocReader
from src.doc_readers.utils import get_document_id_from_filepath
from src.logger import CustomLogger


logger = CustomLogger(__name__)


BASE_URL_REGEX = r'^(.*?)(?=/spaces?)'
CONFLUENCE_URL_REGEX = r'/spaces/([^/]+)(?:/pages/(\d+))?'
class ConfluencePageReader(DocReader):
   def read_documents(self, resource: ConfluenceResource, chatbot_id: str, verbose: bool = False) -> List[Document]:
       self._confluence_url_parser_and_validator(resource)
       confluence = ConfluenceReader(base_url= resource.base_url)
       documents = confluence.load_data(
           space_key=resource.space_key,
           page_ids=resource.page_ids,
           label=resource.label,
           include_attachments=True,
       )
       filtered_documents = []
       for doc in documents:
          
           new_doc_id = get_document_id_from_filepath(
               filepath=doc.metadata['url'],
               chatbot_id=chatbot_id
           )
           doc.id_ = new_doc_id
           page_id = doc.metadata.get('page_id', None)
           #TODO: what if page_id is not present in metadata
           if page_id not in resource.page_ids_to_exclude:
               filtered_documents.append(doc)
       return filtered_documents
  
   def _confluence_url_parser_and_validator(self, resource: ConfluenceResource) -> None:
       url = resource.url
       base_url_match = re.search(BASE_URL_REGEX, url)
       if not base_url_match:
           raise ValueError('Could not extract base url from the provided url')
       resource.base_url = base_url_match.group(1)
      
       match = re.search(CONFLUENCE_URL_REGEX, url)
       if match:
           if match.group(2):
               resource.page_ids = [match.group(2)]
           else:
               resource.space_key = match.group(1)
       provided_fields = sum([bool(resource.space_key), bool(resource.page_ids), bool(resource.label), bool(resource.cql)])
       if provided_fields != 1:
           raise ValueError('Exactly one of space_key, page_ids, label, or cql must be provided')
  

