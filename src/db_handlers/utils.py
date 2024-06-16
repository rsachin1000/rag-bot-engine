import uuid
from datetime import datetime


def get_current_timestamp() -> str:
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def create_unique_id() -> str:
    return str(uuid.uuid4())

