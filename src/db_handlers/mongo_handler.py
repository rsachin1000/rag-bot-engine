from typing import List, Union
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from pydantic import ValidationError

from src import config
from src.db_handlers.db_handler import DBHandler
from src.db_handlers.schemas import (
   BotIndex,
   RagBot,
   ChatSession,
   User,
   Message,
   UserFeedback,
)
from src.logger import CustomLogger


logger = CustomLogger(name=__name__)


class MongoHandler(DBHandler):
   """
   Singleton class: MongoDB implementation of the DBHandler.
   """
   def _init(self):
       self._uri = config.mongo_db_cfg.URI
       self._db_name: str = config.mongo_db_cfg.DBName
       self._collections: config.MongoDBCollections = config.mongo_db_cfg.Collections
      
       self._client = MongoClient(self._uri)
       self._db = self._client[self._db_name]
       self.rag_bot_coll = self._db[config.mongo_db_cfg.Collections.RagBots]
       self.chat_session_coll = self._db[config.mongo_db_cfg.Collections.ChatSessions]
      
       logger.info(
           message="Connected to MongoDB",
           fields={
               "uri": self._uri.split("@")[-1],
               "database": self._db_name,
               "collections": self._collections.model_dump(),
           },
       )
      
   def create_bot(self, bot: RagBot):
       bot_doc = bot.model_dump()
       bot_doc['_id'] = bot_doc.get('bot_id')
       try:
           self.rag_bot_coll.insert_one(bot_doc)
           logger.info(
               message=f"Bot created successfully.",
               fields={"bot_id": bot.bot_id},
           )
       except DuplicateKeyError:
           logger.exception(message="A bot with the same ID already exists.")
      
  
   def update_bot_name(self, bot_id: str, new_name: str) -> bool:
       result = self.rag_bot_coll.update_one(
           {'_id': bot_id},
           {'$set': {'name': new_name}})
      
       return result.modified_count > 0
  
   def update_bot_description(self, bot_id: str, new_description: str) -> bool:
       result = self.rag_bot_coll.update_one(
           {'_id': bot_id},
           {'$set': {'description': new_description}})
      
       return result.modified_count > 0
  
   def get_bot(self, bot_id: str) -> RagBot:
       value= self.rag_bot_coll.find_one({'_id': bot_id})
       value.pop('_id')
       return RagBot(**value)
  
   def get_user_bots(self, email: str) -> List[RagBot]:
       bots=self.rag_bot_coll.find({'user.email': email})
       bot_list=[]
       for bot in bots:
           try:
               bot['bot_id']=bot.pop('_id')
               bot_list.append(RagBot(**bot))
           except ValidationError as e:
               logger.exception(
                   message="parsing error",
                   fields={
                       'error': e.json()
                   }
               )
      
       return bot_list
  
   def get_bot(self, bot_id: str) -> RagBot:
       try:
           bot = self.rag_bot_coll.find_one({'_id': bot_id})
           bot.pop('_id')
           return RagBot(**bot)
       except ValidationError as e:
           logger.exception(
               message= "error in fethcing bot",
               fields={
                   'error': e.json()
               }
           )
  
   def get_all_bots(self) -> List[RagBot]:
       bots=self.rag_bot_coll.find()
       bot_list=[]
       for bot in bots:
           try:
               bot.pop('_id')
               bot_list.append(RagBot(**bot))
           except ValidationError as e:
               logger.exception(
                   message="parsing error",
                   fields={
                       'error': e.json()
                   }
               )
       return bot_list
  
   def update_bot_status(self, bot_id: str, status: bool) -> bool:
       result = self.rag_bot_coll.update_one(
           {'_id': bot_id},
           {'$set': {'ready': status}})
      
       return result.modified_count > 0
  
   def _update_bot_indexes(self, bot_id: str, indexes: List[BotIndex]) -> bool:
       indexes_dicts = [index.model_dump() for index in indexes]
       try:
           result = self.rag_bot_coll.update_one(
               {'_id': bot_id},
               {'$set': {'indexes': indexes_dicts}}
           )
           return result.modified_count > 0
      
       except Exception as e:
           logger.exception(
               message="failed to update indexing for bot",
               fields={
                   'bot_id': bot_id,
                   'error': str(e)
               }
           )
           return False
  
   def _create_chat_session(self, chat_session: ChatSession) -> bool:
       chat_session_dict = chat_session.model_dump()
       chat_session_dict['_id'] = chat_session_dict['chat_session_id']
       if not self._bot_exists(chat_session_dict['bot_id']):
           logger.exception(
               message="bot doesn't exist",
               fields={
                   'bot_id': chat_session.bot_id,
               }
           )
           return False
      
       try:
           output = self.chat_session_coll.insert_one(chat_session_dict)
           return bool(output.inserted_id)
       except DuplicateKeyError:
           logger.exception(
               message="session already exists",
               fields={
                   'bot_id': chat_session.bot_id,
                   'session_id': chat_session.chat_session_id
               }
           )
           return False
  
   def update_chat_session_name(
       self, bot_id, chat_session_id: str, updated_name: str
   ) -> bool:
       try:
           result = self.chat_session_coll.update_one(
               {'_id': chat_session_id},
               {'bot_id': bot_id},
               {'$set': {'name': updated_name}}
           )
           return result.modified_count > 0
       except Exception as e:
           logger.exception(message=f"An error occurred: {e}")
           return False
  
   def _insert_chat_session_feedback(
       self, bot_id:str, chat_session_id: str, feedback: UserFeedback
   ) -> bool:
       """
       Insert feedback for a chat session.
       """
       try:
           result = self.chat_session_coll.update_one(
               {"bot_id": bot_id, '_id': chat_session_id},
               {'$push': {'feedbacks': feedback.model_dump()}}
           )
           return result.modified_count > 0
       except Exception as e:
           logger.exception(
               message=f"failed to insert session feedback in chat session",
               fields={
                   'chat_session_id': chat_session_id,
                   'error': str(e),
               })
           return False
  
   def get_chat_session(self, chat_session_id: str) -> Union[ChatSession, None]:
       session_doc = self.chat_session_coll.find_one({'_id': chat_session_id})
       if session_doc:
           return ChatSession(**session_doc)
       else:
           return None
  
   def get_all_chat_session(self, bot_id: str) -> List[ChatSession]:
       session_docs = self.chat_session_coll.find({"bot_id": bot_id})
       if session_docs:
           chat_sessions=[]
           for session in session_docs:
               session.pop('_id')
               chat_sessions.append(ChatSession(**session))
           return chat_sessions
       else:
           return None
  
   def get_user_sessions(self, user: User, bot_id: str) -> List[ChatSession]:
       """
       Get all sessions for a user belonging to the given bot id.
       """
       sessions_docs = self.chat_session_coll.find({
           'user.email': user.email,
           'bot_id': bot_id
       })
       sessions_list = []
       for session in sessions_docs:
           try:
               sessions_list.append(ChatSession(**session))
           except ValidationError as e:
               logger.exception(f"Failed to parse ChatSession data: {e.json()}")
       return sessions_list
  
   def _insert_message_feedback(
       self, bot_id: str, chat_session_id: str, message_id: str, feedback: UserFeedback
   ) -> bool:
       """
       Add feedback to a message.
       """
       try:
           if not self._chat_message_exists(
               bot_id=bot_id, chat_session_id=chat_session_id, message_id=message_id
           ):
               raise ValueError(f"Either the bot with id: {bot_id} does not exist, "
                   f"or the chat session with id: {chat_session_id} does not exist, "
                   f"or the message with id: {message_id} does not exist.")
          
           result = self.chat_session_coll.update_one(
               {'_id': chat_session_id, 'messages.message_id': message_id},
               {'$push': {'messages.$.feedbacks': feedback.model_dump()}}
           )
           return result.modified_count > 0
       except Exception as e:
           logger.exception(
               message=f"failed to insert feedback",
               fields={
                   'chat_session_id': chat_session_id,
                   'message_id': message_id,
                   'error': str(e),
               }
           )
           return False
  
   def _create_message(self, chat_session_id: str, message: Message) -> bool:
       """
       Create a new message.
       """
       message_dict = message.model_dump()
       try:
           result = self.chat_session_coll.update_one(
               {'_id': chat_session_id},
               {'$push': {'messages': message_dict}}
           )
           return result.modified_count > 0
       except Exception as e:
           logger.exception(
               message=f"failed to create a new message in chat session",
               fields={
                   'chat_session_id': chat_session_id,
                   'error': str(e),
               }
           )
           return False
  
   def _bot_exists(self, bot_id: str) -> bool:
       result = self.rag_bot_coll.find_one({'_id': bot_id})
       return bool(result)
  
   def _chat_session_exists(self, bot_id: str, chat_session_id) -> bool:
       result = self.chat_session_coll.find_one({'_id': chat_session_id, 'bot_id': bot_id})
       return bool(result)

   def _chat_message_exists(self, bot_id: str, chat_session_id: str, message_id: str) -> bool:
       result = self.chat_session_coll.find_one({
           '_id': chat_session_id,
           'bot_id': bot_id,
           'messages': {
               '$elemMatch': {
                   'message_id': message_id
               }
           }
       })
       return bool(result)

