from src.db_handlers.db_handler import DBHandler
from src.db_handlers.mongo_handler import MongoHandler
from src.db_handlers.schemas import (
   User,
   BotConfig,
   RagBot,
)
from src.config_constants import MONGO_DB


def get_db_handler(db_type: str) -> DBHandler:
   """
   Factory function to get the DBHandler instance.
   """
   if db_type == MONGO_DB:
       return MongoHandler.get_instance()
   else:
       raise ValueError(f"DB type {db_type} not supported")

