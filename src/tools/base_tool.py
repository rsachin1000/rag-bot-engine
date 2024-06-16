from abc import ABC, abstractmethod


class BaseTool(ABC):
   @classmethod
   @abstractmethod
   def from_defaults(cls, *args, **kwargs):
       """Use this method to create a new instance of the tool with default settings.


       Raises:
           NotImplementedError: _description_
       """
      
       raise NotImplementedError
  
