from enum import Enum
from typing import List, Dict, Optional, Any, Union

from pydantic import model_validator, Field, BaseModel

from src import config
from src.db_handlers.utils import get