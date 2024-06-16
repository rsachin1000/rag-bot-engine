from abc import ABC, abstractmethod
from typing import List, Union, Dict


from src.db_handlers.schemas import (
   BotIndex,
   RagBot,
   ChatSession,
   User,
   FeedbackLabel,
   Message,
   MessageCreatorRole,
   UserFeedback,
   SourceNodeWithScore,
)
from src.db_handlers.utils import create_unique_id


class DBHandler(ABC):
   """
   Singleton Class: Base class for database handlers.
   """
  
   _instance = None
   _calling_from_handler: bool = False
  
   @classmethod
   def get_instance(cls, *args, **kwargs):
       """
       Get the singleton instance. If it doesn't exist, create it.
       """
       if cls._instance is None:
           cls._calling_from_handler = True
           cls._instance = cls(*args, **kwargs)
           cls._calling_from_handler = False
       return cls._instance


   def __init__(self):
       if not self._calling_from_handler:
           raise RuntimeError(
               'This class is a singleton. Use get_instance() to get an instance of the class.'
           )
       self._init()
      
   @abstractmethod
   def _init(self):
       """
       Initialize the database handler.
       """
       raise NotImplementedError
  
   @staticmethod
   def new_chat_session_id() -> str:
       """
       Generate a new session id.
       """
       return create_unique_id()
  
   @abstractmethod
   def create_bot(self, bot: RagBot):
       raise NotImplementedError
  
   @abstractmethod
   def update_bot_name(self, bot_id: str, new_name: str):
       raise NotImplementedError
  
   @abstractmethod
   def update_bot_description(self, bot_id: str, new_description: str):
       raise NotImplementedError
  
   @abstractmethod
   def get_bot(self, bot_id: str) -> RagBot:
       raise NotImplementedError
  
   @abstractmethod
   def get_user_bots(self, email: str) -> List[RagBot]:
       raise NotImplementedError
  
   @abstractmethod
   def get_bot(self, bot_id: str) -> RagBot:
       raise NotImplementedError
  
   @abstractmethod
   def get_all_bots(self) -> List[RagBot]:
       raise NotImplementedError
  
   @abstractmethod
   def update_bot_status(self, bot_id: str, status: bool):
       raise NotImplementedError
  
   @abstractmethod
   def _update_bot_indexes(self, bot_id: str, indexes: List[BotIndex]):
       raise NotImplementedError
  
   def update_bot_indexes(self, bot_id: str, resource_to_index_map: Dict[str, str]):
       indexes = []
       for resource, index_id in resource_to_index_map.items():
           indexes.append(BotIndex(resource=resource, index_id=index_id))
      
       self._update_bot_indexes(bot_id=bot_id, indexes=indexes)
      
   @abstractmethod
   def _create_chat_session(self, chat_session: ChatSession):
       """
       Create a new chat session.
       """
       raise NotImplementedError
  
   def create_session(
       self, bot_id: str,  user: User, chat_session_id: str = None, chat_session_name: str = None
   ) -> ChatSession:
       """
       Create a new chat session.
       """
       if not self._bot_exists(bot_id = bot_id):
           raise ValueError(f"Bot with id: {bot_id} does not exist.")
       if chat_session_id == None:
           chat_session_id = self.new_chat_session_id()
       session_obj = ChatSession(
           chat_session_id=chat_session_id,
           bot_id=bot_id,
           name=chat_session_name,
           user=user
       )
       self._create_chat_session(chat_session=session_obj)
       return session_obj
  
   @abstractmethod
   def update_chat_session_name(self, bot_id, chat_session_id: str, updated_name: str):
       """
       Update the name of a session.
       """
       raise NotImplementedError
  
   @abstractmethod
   def _insert_chat_session_feedback(self, chat_session_id: str, feedback: UserFeedback):
       """
       Insert feedback for a chat session.
       """
       raise NotImplementedError
  
   def insert_chat_session_feedback(
       self,
       bot_id: str,
       chat_session_id: str,
       user: User,
       text: str = "",
       label: FeedbackLabel = FeedbackLabel.NOT_SET,
   ):
       """
       Append user feedback to a chat session.
       """
       if not self._chat_session_exists(bot_id=bot_id, chat_session_id=chat_session_id):
               raise ValueError(f"Either the bot with id: {bot_id} does not exist "
                               f"or the chat session with id: {chat_session_id} does not exist.")
      
       feedback = UserFeedback(user=user, feedback_text=text, feedback_label=label)
       return self._insert_chat_session_feedback(bot_id=bot_id, chat_session_id=chat_session_id, feedback=feedback)
  
   @abstractmethod
   def get_chat_session(self, chat_session_id: str) -> Union[ChatSession, None]:
       """
       Get a session.
       """
       raise NotImplementedError
  
   @abstractmethod
   def get_all_chat_session(self, bot_id: str) -> List[ChatSession]:
       """
       Get all sessions.
       """
       raise NotImplementedError
  
   @abstractmethod
   def get_user_sessions(self, user: User, bot_id: str) -> List[ChatSession]:
       """
       Get all sessions for a user belonging to the given bot id.
       """
       raise NotImplementedError
  
   @abstractmethod
   def _insert_message_feedback(self, chat_session_id: str, message_id: str, feedback: UserFeedback):
       """
       Insert feedback for a message.
       """
       raise NotImplementedError
  
   def insert_message_feedback(
       self,
       bot_id: str,
       chat_session_id: str,
       message_id: str,
       user: User,
       text: str = "",
       label: FeedbackLabel = FeedbackLabel.NOT_SET
   ):
       """
       Add feedback to a message.
       """
       feedback = UserFeedback(user=user, feedback_text=text, feedback_label=label)
       return self._insert_message_feedback(
           bot_id, chat_session_id=chat_session_id, message_id=message_id, feedback=feedback
       )
  
   @abstractmethod
   def _create_message(self, chat_session_id: str, message: Message):
       """
       Create a new message.
       """
       raise NotImplementedError
  
   def create_message(
       self,
       chat_session_id: str,
       text: str,
       role: MessageCreatorRole,
       sources_nodes: List[SourceNodeWithScore] = None
   ):
       message_obj = Message.from_role(role=role, text=text, source_nodes=sources_nodes)
       self._create_message(chat_session_id=chat_session_id, message=message_obj)


