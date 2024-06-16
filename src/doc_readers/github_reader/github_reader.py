import re
from typing import List, Dict

from llama_index.core import Document
from llama_index.readers.github import GithubClient

from src import config
from src.doc_readers.doc_reader import DocReader
from src.doc_readers.utils import get_document_id_from_filepath
from src.db_handlers.schemas import GithubResource
from src.logger import CustomLogger
from src.doc_readers.github_reader.github_repo_reader import GithubRepositoryReader


logger = CustomLogger(name=__name__)


DIRECTORY_FILTER_TYPE = GithubRepositoryReader.FilterType.EXCLUDE
FILE_FILTER_TYPE = GithubRepositoryReader.FilterType.INCLUDE
GITHUB_URL_REGEX = r"https://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?"


class GithubReader(DocReader):
   def __init__(self) -> None:
       super().__init__()
       self.github_client= GithubClient(github_token=config.app_cfg.GithubAccessToken, verbose=True)
  
   async def read_documents(
       self, resource: GithubResource, chatbot_id: str, verbose: bool = False
   ) -> List[Document]:
       parsed_url = self._parse_github_url(resource)
       github_reader = GithubRepositoryReader(
               github_client=self.github_client,
               owner=parsed_url['owner'],
               repo=parsed_url['repo'],
               use_parser=False,
               filter_directories=(
                       resource.directory_types_to_exclude,
                       DIRECTORY_FILTER_TYPE
                   ),
               filter_file_extensions=(
                   resource.file_types_to_include,
                   FILE_FILTER_TYPE,
               ),
               verbose=verbose,
           )
      
       documents = await github_reader.load_data(branch=parsed_url['branch'])
      
       for doc in documents:
           # Todo: check if file_name is complete filepath or not
           new_doc_id = get_document_id_from_filepath(
               filepath=doc.metadata['url'],
               chatbot_id=chatbot_id
           )
           doc.id_ = new_doc_id
      
       return documents
  
   def _parse_github_url(self, resource: GithubResource) -> Dict[str, str]:
       try:
           match = re.match(GITHUB_URL_REGEX, resource.url)
           if not match:
               raise ValueError("Invalid GitHub URL format.")
           return {
               'owner': match.group(1),
               'repo': match.group(2),
               'branch': match.group(3) if match.group(3) else 'main'
           }
       except Exception as e:
           logger.error(message=f"Error parsing URL: {e}")
  
  
