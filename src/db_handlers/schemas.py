from enum import Enum
from typing import List, Dict, Optional, Any

from pydantic import model_validator, Field, BaseModel

from src import config
from src.db_handlers.utils import get_current_timestamp, create_unique_id


class User(BaseModel):
    name: Optional[str] = Field(default=None, title="name of the user creating the bot")
    email: str = Field(title="email of the user")

    @model_validator(mode="before")
    def check_email(cls, values: Dict[str, str]):
        if not values.get('email'):
            raise ValueError('Email is required')
        
        if not values.get('name'):
            values['name'] = values['email'].split('@')[0]

        return values
    

class CrawlResource(BaseModel):
    url: str = Field(title="url of the resource to be crawled")
    description: str = Field(title="description of the resource")


class ConfluenceResource(CrawlResource):
    base_url: Optional[str] = None
    space_key: Optional[str] = None
    page_ids: List[str] = Field(default_factory=list, title="list of page ids to crawl")
    label: Optional[str] = None
    cql: Optional[str] = None
    page_ids_to_exclude: List[str] = Field(
        default_factory=list, title="list of page ids to exclude"
    )


class GithubResource(CrawlResource):
    directory_types_to_exclude: List[str] = Field(default_factory=list)
    file_types_to_include: List[str] = Field(default=['.md', '.txt', '.ipynb'])


class BotConfig(BaseModel):
    name: str = Field(title="name of the bot")
    description: Optional[str] = Field(default=None, title="description of the bot")
    llm_model_name: str = Field(title="name of the language model to use")
    embeddings_model_name: str = Field(title="name of the embeddings model to use")
    github_resources: List[GithubResource] = Field(default_factory=list)
    confluence_resources: List[ConfluenceResource] = Field(default_factory=list)
    user: User = Field(title="user creating the bot")

    @model_validator(mode="before")
    def validate(cls, values: Dict[str, Any]):
        if not values.get("llm_model_name"):
            values["llm_model_name"] = config.openai_cfg.DefaultLLM

        if not values.get("embeddings_model_name"):
            values["embeddings_model_name"] = config.openai_cfg.DefaultEmbeddingsModel
        
        return values
    

class BotIndex(BaseModel):
    resource: str
    index_id: str


class RagBot(BaseModel):
    bot_id: str = Field(title="unique id of the bot")
    name: str = Field(title="name of the bot")
    description: Optional[str] = Field(default=None, title="description of the bot")
    llm_model: str = Field(title="name of the language model to use")
    embeddings_model: str = Field(title="name of the embeddings model to use")
    user: User = Field(title="user creating the bot")
    created_at: str = Field(title="timestamp when the bot was created")
    updated_at: str = Field(title="timestamp when the bot was last updated")
    crawl_resources: List[CrawlResource] = Field(
        default_factory=list, title="list of resources to crawl"
    )
    indexes: List[BotIndex] = Field(
        default_factory=list, title="a mapping of resource to index id"
    )
    ready: bool = Field(default=False, title="flag to indicate if the bot is ready")

    @model_validator(mode="before")
    def validate(cls, values: Dict[str, Any]):
        if not values.get("bot_id"):
            values["bot_id"] = create_unique_id()
        
        curr_time = get_current_timestamp()
        if not values.get("created_at"):
            values["created_at"] = curr_time
        
        if not values.get("updated_at"):
            values["updated_at"] = curr_time
        
        return values

    @classmethod
    def from_bot_config(cls, bot_config: BotConfig) -> 'RagBot':
        crawl_resources = bot_config.github_resources + bot_config.confluence_resources
        return cls(
            name=bot_config.name,
            description=bot_config.description,
            llm_model=bot_config.llm_model_name,
            embeddings_model=bot_config.embeddings_model_name,
            user=bot_config.user,
            crawl_resources=crawl_resources
        )
    
    @property
    def id(self) -> str:
        return self.bot_id
    

class FeedbackLabel(str, Enum):
    LIKED = "liked"
    DISLIKED = "disliked"
    NOT_SET = "not_set"


class UserFeedback(BaseModel):
    user: User = Field(title="user providing the feedback")
    feedback_text: Optional[str] = Field(default=None, title="additional feedback text")
    feedback_label: FeedbackLabel = Field(
        default=FeedbackLabel.NOT_SET, title="feedback label"
    )


class MessageCreatorRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class SourceNodeWithScore(BaseModel):
    node_id: str = Field(title="node id of the source node")
    url: str = Field(title="url of the original source which the node is derived from")
    score: float = Field(title="score of the source node")


class Message(BaseModel):
    message_id: str = Field(title="unique id of the message")
    text: str = Field(title="text of the message")
    role: MessageCreatorRole = Field(title="role of the message creator")
    created_at: str = Field(title="timestamp when the message was created")
    feedbacks: List[UserFeedback] = Field(
        default_factory=list, title="feedback provided by the user"
    )
    source_nodes: Optional[List[SourceNodeWithScore]] = Field(
        default=None, title="nodes which are sent to the llm as context"
    )

    @model_validator(mode="before")
    def validate(cls, values: Dict[str, Any]):
        if not values.get("message_id"):
            values["message_id"] = create_unique_id()
        
        if not values.get("created_at"):
            values["created_at"] = get_current_timestamp()
        
        return values
    
    @classmethod
    def from_role(
        cls,
        role: MessageCreatorRole,
        text: str,
        source_nodes: Optional[List[SourceNodeWithScore]] = None,
    ) -> 'Message':
        return cls(
            text=text,
            role=role,
            source_nodes=source_nodes
        )
    
    @property
    def id(self) -> str:
        return self.message_id
    

class ChatSession(BaseModel):
    chat_session_id: str = Field(title="unique id of the chat session")
    name: str = Field(title="name of the chat session")
    bot_id: str = Field(title="id of the bot")
    messages: List[Message] = Field(
        default_factory=list, title="list of messages exchanged in the session"
    )
    created_at: str = Field(title="timestamp when the chat session was created")
    updated_at: str = Field(title="timestamp when the chat session was last updated")
    user: User = Field(title="user creating the chat session")
    feedbacks: List[UserFeedback] = Field(
        default_factory=list, title="feedback provided by the user"
    )

    @model_validator(mode="before")
    def validate(cls, values: Dict[str, Any]):
        curr_time = get_current_timestamp()
        if not values.get("created_at"):
            values["created_at"] = curr_time
        
        if not values.get("updated_at"):
            values["updated_at"] = curr_time
        
        return values
    
    @property
    def id(self) -> str:
        return self.chat_session_id

