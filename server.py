import time
import uuid
import argparse
import uvicorn
from fastapi import FastAPI, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi import HTTPException

from io_schemas import *
from src import config
from src.chat_bot_manager import ChatBotManager
from src.db_handlers.schemas import BotConfig, FeedbackLabel, RagBot, User
from src.logger import CustomLogger
from version import VERSION


logger = CustomLogger(__name__)


# Read config and env file paths from command line arguments
parser = argparse.ArgumentParser(description='Chat Cohorts Application')
parser.add_argument(
   '--config',
   type=str,
   help='config file path',
   default="configs/dev.config.json",
)
parser.add_argument('--env', type=str, help='env file path', default=".env")


args = parser.parse_args()


# Load config and env files
config.load_config(
   app_version=VERSION,
   config_json_path=args.config,
   env_path=args.env
)

app = FastAPI()
chatbot_manager= ChatBotManager()

"""
APIs to implement:
1. Create a new chatbot (given a config file containing list of resources, \
   chat_bot name, chat_bot description, llm_model, etc.)
2. Get a list of all chatbots
3. Get a list of all chatbots belonging to a particular user (given user_id)
4. Get a new chat_session_id (given bot_id)
5. Answer a user query (given chat_session_id, user_query, bot_id)
   - if the chat_session is not already created, create a new chat_session \
       with first 20 characters of user_query as chat_session_name
6. Get a list of all chat_sessions belonging to a particular chatbot (given bot_id)
7. Get a list of all chat_sessions belonging to a particular user (given user_id, bot_id)
8. Update bot name and description (given bot_id) (2 separate APIs)
9. Update chat_session name (given chat_session_id, updated_name, bot_id)
10. Insert chat_message_feedback (given chat_session_id, chat_message_id, \
   feedback: containing Comment and Label)
11. Insert chat_session_feedback (given chat_session_id, feedback: containing Comment and Label)
"""


app.add_middleware(
   CORSMiddleware,
   allow_origins=["*"],  # Allow all origins (You can adjust this based on your requirements)
   allow_credentials=True,
   allow_methods=["GET", "POST", "PUT", "DELETE"],  # Allow specific HTTP methods
   allow_headers=["*"],  # Allow all headers (You can adjust this based on your requirements)
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
   start_time = time.time()
   # Generate a unique request ID
   request_id = str(uuid.uuid4())
   request.state.request_id = request_id
  
   response = await call_next(request)
   process_time = time.time() - start_time
  
   response.headers["X-Request-ID"] = request_id
   response.headers["X-Process-Time"] = str(process_time)
   return response


@app.get("/healthcheck")
def healthcheck():
   return HealthCheckResponse(status='ok')


@app.post("/create_chatbot")
async def create_chatbot(config: BotConfig, request: Request) -> CreateChatBotOutput:
   try:
       bot = await chatbot_manager.create_new_bot(config)
       return CreateChatBotOutput(bot)
   except Exception as e:
       logger.exception(
           message="failed to create chatbot",
           fields={
               "request_id": request.state.request_id,
               "error": str(e),
           }
       )
       raise HTTPException(status_code=400)


@app.get('/get_bot')
def get_bot(bot_id: str, request: Request):
   try:
       bot = chatbot_manager._db_handler.get_bot(bot_id)
       return ChatBotOutput(bot)
   except Exception as e:
       logger.exception(
           message="failed to retrieve bot",
           fields={
               "request_id": request.state.request_id,
               "error": str(e),
           }
       )
       raise HTTPException(status_code=404, detail="bot not found")


@app.get("/get_all_bots")
def get_all_bots(request: Request):
   try:
       bots: RagBot = chatbot_manager._db_handler.get_all_bots()
       bots_output = [ChatBotOutput(bot) for bot in bots]
       return bots_output
   except Exception as e:
       logger.exception(
           message="failed to retrieve bots",
           fields={
               "request_id": request.state.request_id,
               "error": str(e),
           }
       )
       raise HTTPException(status_code=500)


@app.get("/get_user_bots")
def list_user_chatbots(user_email_id: str, request: Request):
   try:
       bots: RagBot = chatbot_manager._db_handler.get_user_bots(email=user_email_id)
       bots_output = [ChatBotOutput(bot) for bot in bots]
       return bots_output
   except Exception as e:
       logger.exception(
           message="failed to retrieve bots",
           fields={
               "request_id": request.state.request_id,
               "error": str(e),
           }
       )
       raise HTTPException(status_code=404, detail="user not found")


@app.get("/new_chat_session_id")
def new_chat_session_id(request: Request):
   try:
       chat_session_id = chatbot_manager._db_handler.new_chat_session_id()
       return GetChatSessionIdResponse(chat_session_id=chat_session_id)
   except Exception as e:
       logger.exception(
           message="failed to generate new chat session id",
           fields={
               "request_id": request.state.request_id,
               "error": str(e),
           }
       )
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.post("/chat")
async def chat(
   request: Request,
   bot_id: str,
   chat_session_id: str, 
   request_body: ChatRequest,
   email: str,
   username: str = None,
):
   user_obj = User(email=email, username=username)
   try:
       llm_response = await chatbot_manager.chat(
           user_query=request_body.query,
           bot_id=bot_id,
           chat_session_id=chat_session_id,
           user=user_obj,
       )
       return ChatResponse.from_agent_response(response=llm_response)
   except Exception as e:
       logger.exception(
           message="failed to chat",
           fields={
               "request_id": request.state.request_id,
               "error": str(e),
           }
       )
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
      

@app.post("/stream_chat")
async def stream_chat(
   request: Request,
   bot_id: str,
   chat_session_id: str, 
   request_body: ChatRequest,
   email: str,
   username: str = None,
):
   user_obj = User(email=email, username=username)
   try:
       content_stream = await chatbot_manager.stream_chat(
           user_query=request_body.query,
           bot_id=bot_id,
           chat_session_id=chat_session_id,
           user=user_obj,
       )
       return StreamingResponse(content_stream, media_type="text/event-stream")
   except Exception as e:
       logger.exception(
           message="failed to chat",
           fields={
               "request_id": request.state.request_id,
               "error": str(e),
           }
       )
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/get_all_chat_session")
def get_all_chat_session(bot_id: str, request: Request):
   try:
       chat_sessions = chatbot_manager._db_handler.get_all_chat_session(bot_id=bot_id)
       return chat_sessions
   except Exception as e:
       logger.exception(
           message="failed to retrieve chat sessions",
           fields={
               "request_id": request.state.request_id,
               "error": str(e),
           }
       )
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.post("/get_chat_session_by_user")
def get_chat_session_by_user(bot_id: str, user: User, request: Request):
   try:
       chat_sessions = chatbot_manager._db_handler.get_user_sessions(
           bot_id=bot_id, user=user
       )
       return chat_sessions
   except Exception as e:
       logger.exception(
           message="failed to retrieve chat sessions",
           fields={
               "request_id": request.state.request_id,
               "error": str(e),
           }
       )
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/update_bot_name")
def update_bot_name(bot_id: str, new_name: str, request: Request):
   try:
       updated_bot = chatbot_manager._db_handler.update_bot_name(
           bot_id = bot_id, new_name= new_name
       )
       return BotNameUpdateResponse(status=updated_bot)
   except Exception as e:
       logger.exception(
           message="failed to update bot name",
           fields={
               "request_id": request.state.request_id,
               "error": str(e),
           }
       )
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/update_bot_description")
def update_bot_description(bot_id: str, new_description: str, request: Request):
   try:
       updated_bot = chatbot_manager._db_handler.update_bot_description(
           bot_id = bot_id, new_description= new_description
       )
       return BotDescUpdateResponse(status=updated_bot)
   except Exception as e:
       logger.exception(
           message="failed to update bot description",
           fields={
               "request_id": request.state.request_id,
               "error": str(e),
           }
       )
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.get("/update_chat_session_name")
def update_chat_session_name(
   bot_id: str, chat_session_id: str, new_name: str, request: Request
):
   try:
       updated_bot = chatbot_manager._db_handler.update_chat_session_name(
           bot_id=bot_id, chat_session_id=chat_session_id, new_name=new_name
       )
       return updated_bot
   except Exception as e:
       logger.exception(
           message="failed to update chat session name",
           fields={
               "request_id": request.state.request_id,
               "error": str(e),
           }
       )
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.post("/insert_chat_session_feedback")
def insert_chat_session_feedback(
   bot_id: str,
   session_id: str,
   user: User,
   request: Request,
   comment: str = None,
   label: FeedbackLabel = None,
):
   try:
       if comment is not None or label is not None:
           if label is None: label= FeedbackLabel.NotSet
           feedback = chatbot_manager._db_handler.insert_chat_session_feedback(
               bot_id=bot_id,
               chat_session_id=session_id,
               user=user,
               text=comment,
               label=label,
           )
           return InsertChatSessionFeedbackResponse(status=feedback)
       else:
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail="at least one of comment or label should be provided"
           )
   except Exception as e:
       logger.exception(
           message="failed to insert chat session feedback",
           fields={
               "request_id": request.state.request_id,
               "error": str(e),
           }
       )
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@app.post("/insert_chat_message_feedback")
def insert_chat_message_feedback(
   bot_id: str,
   session_id: str,
   message_id: str,
   user: User,
   request: Request,
   comment: str = None,
   label: FeedbackLabel = None,
):
   try:
       if comment or label is not None:
           if label is None: label= FeedbackLabel.NotSet
           feedback = chatbot_manager._db_handler.insert_message_feedback(
               bot_id=bot_id,
               chat_session_id=session_id,
               message_id=message_id,
               user = user,
               text= comment,
               label= label
           )
           return InsertChatMessageFeedbackResponse(status=feedback)
       else:
           raise HTTPException(
               status_code=status.HTTP_400_BAD_REQUEST,
               detail="at least one of comment or label should be provided"
           )
   except Exception as e:
       logger.exception(
           message="failed to insert message feedback",
           fields={
               "request_id": request.state.request_id,
               "error": str(e),
           }
       )
       raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


uvicorn.run(app, host=config.app_cfg.Host, port=config.app_cfg.Port)
