from pydantic import BaseModel, Field

class Message(BaseModel):
    sender: str
    receiver: str
    content: str

class MessageInDB(Message):
    id: str = Field(..., alias="_id")
