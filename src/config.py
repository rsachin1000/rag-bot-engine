import os
import json
from typing import Optional

from pydantic import Field, BaseModel
from dotenv import load_dotenv

from src.logger import CustomLogger
from src.config_constants import MONGO_DB, CHROMA_DB


logger = CustomLogger(__name__)


class APPCfg(BaseModel):
    Host: str = Field(description="Host of the application")
    Port: int = Field(description="Port of the application")
    Version: str = Field(description="Version of the application")
    DbStore: str = Field(
        description="DB to be used for storing ragbot metadata, docstore, and index store"
    )
    GithubAccessToken: Optional[str] = Field(description="for accessing github api")


class OpenAICfg(BaseModel):
    DefaultLLM: str = Field(description="Default LLM to be used for generating responses")
    DefaultEmbeddingsModel: str = Field(
        description="Default model to be used for embeddings generation"
    )


class MongoDBCollections(BaseModel):
    RagBots: str = Field(description="Collection to store ragbot metadata")
    ChatSessions: str = Field(description="Collection to store chat sessions")


class MongoDBCfg(BaseModel):
    URI: str = Field(description="MongoDB URI connection string")
    DBName: str = Field(description="Name of the MongoDB database")
    Collections: MongoDBCollections = Field(description="Collections in the MongoDB")


class LlamaDocstoreCfg(BaseModel):
    DbName: str = Field(description="Name of the database for storing documents")
    Namespace: str = Field(description="Namespace for stored documents")


class LlamaIndexStoreCfg(BaseModel):
    DbName: str = Field(description="Name of the database for storing indexes")
    Namespace: str = Field(description="Namespace for stored indexes")


class LlamaVectorStoreCfg(BaseModel):
    DirPath: str = Field(description="Directory path for storing vectors")
    DbName: str = Field(description="Name of the database for storing vectors")
    CollectionName: str = Field(description="Name of the collection for storing vectors")


class LlamaIndexCfg(BaseModel):
    MongoURI: Optional[str] = Field(
        description="MongoDB URI connection string for docstore and indexstore"
    )
    DocStoreType: str = Field(description="Type of docstore to be used")
    VectorStoreType: str = Field(description="Type of vector store to be used")
    DocStore: LlamaDocstoreCfg = Field(description="Configuration for docstore")
    IndexStore: LlamaIndexStoreCfg = Field(description="Configuration for index store")
    VectorStore: LlamaVectorStoreCfg = Field(description="Configuration for vector store")


app_cfg: APPCfg
openai_cfg: OpenAICfg
mongo_db_cfg: MongoDBCfg
llama_index_cfg: LlamaIndexCfg


CONFIG_FILEPATH_ENV_VAR = "CONFIG_FILEPATH"


def load_config(app_version: str, config_json_path: str, env_path: str):
    load_dotenv(dotenv_path=env_path)
    logger.info(f"loaded env vars from `{env_path}`")

    config_json_path = os.getenv(CONFIG_FILEPATH_ENV_VAR, config_json_path)
    logger.info(f"loading config from `{config_json_path}`")
    with open(config_json_path, "r") as f:
        config = json.load(f)

    global app_cfg, openai_cfg, mongo_db_cfg, llama_index_cfg

    app_cfg = APPCfg(
        Host=config["Host"],
        Port=config["Port"],
        Version=app_version,
        DbStore=config["DbStore"],
        GithubAccessToken=os.getenv("GITHUB_ACCESS_TOKEN", None),
    )
    app_cfg_dict = app_cfg.model_dump()
    app_cfg_dict["GithubAccessToken"] = "********"
    logger.info(message="loaded app config", fields=app_cfg_dict)

    openai_cfg = OpenAICfg(
        DefaultLLM=config["OpenAI"]["DefaultLLM"],
        DefaultEmbeddingsModel=config["OpenAI"]["DefaultEmbeddingsModel"],
    )
    logger.info(
        message="loaded openai config", fields=openai_cfg.model_dump()
    )

    if app_cfg.DbStore == MONGO_DB:
        mongo_db_cfg = MongoDBCfg(
            URI=os.environ.get("MONGO_DB_URI", None),
            DBName=config["MongoDB"]["DBName"],
            Collections=MongoDBCollections(
                RagBots=config["MongoDB"]["Collections"]["RagBots"],
                ChatSessions=config["MongoDB"]["Collections"]["ChatSessions"],
            ),
        )

        mongo_db_cfg_dict = mongo_db_cfg.model_dump()
        mongo_db_cfg_dict["URI"] = mongo_db_cfg_dict["URI"].split("@")[-1]
        logger.info(
            message="loaded mongo db config", fields=mongo_db_cfg_dict
        )

    index_store_cfg = None
    docstore_cfg = None

    if config["LlamaIndex"]["DocStoreType"] == MONGO_DB:
        index_store_cfg = LlamaIndexStoreCfg(
            DbName=config["LlamaIndex"]["IndexStore"]["MongoDB"]["DBName"],
            Namespace=config["LlamaIndex"]["IndexStore"]["MongoDB"]["Namespace"]
        )

        docstore_cfg = LlamaDocstoreCfg(
            DbName=config["LlamaIndex"]["DocStore"]["MongoDB"]["DBName"],
            Namespace=config["LlamaIndex"]["DocStore"]["MongoDB"]["Namespace"]
        )

    vector_store_cfg = None
    if config["LlamaIndex"]["VectorStoreType"] == CHROMA_DB:
        vector_store_cfg = LlamaVectorStoreCfg(
            DirPath=config["LlamaIndex"]["VectorStore"]["ChromaDB"]["DirPath"],
            DbName=config["LlamaIndex"]["VectorStore"]["ChromaDB"]["DBName"],
            CollectionName=config["LlamaIndex"]["VectorStore"]["ChromaDB"]["CollectionName"]
        )

    llama_index_cfg = LlamaIndexCfg(
        MongoURI=os.environ.get("MONGO_DB_URI", None),
        DocStoreType=config["LlamaIndex"]["DocStoreType"],
        VectorStoreType=config["LlamaIndex"]["VectorStoreType"],
        DocStore=docstore_cfg,
        IndexStore=index_store_cfg,
        VectorStore=vector_store_cfg,
    )

    llama_index_cfg_dict = llama_index_cfg.model_dump()
    llama_index_cfg_dict["MongoURI"] = llama_index_cfg_dict["MongoURI"].split('@')[-1]
    logger.info(
        message="llama index config loaded",
        fields=llama_index_cfg_dict
    )

    return config

