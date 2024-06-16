import hashlib


def get_document_id_from_filepath(filepath: str, chatbot_id: str) -> str:
   """Get the document id from the filepath and chatbot_id. Chatbot ID is also used
   to handle the cases where the same document is used by multiple chatbots.


   Args:
       filepath (str): complete file path of the document
       chatbot_id (str): chat bot id for which the document is being created


   Returns:
       str: hash of the chatbot_id and filepath
   """
   str_to_hash = f"{chatbot_id}-{filepath}"
   return hashlib.sha256(str_to_hash.encode()).hexdigest()
