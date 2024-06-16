import uuid


def create_unique_id() -> str:
    return str(uuid.uuid4())

