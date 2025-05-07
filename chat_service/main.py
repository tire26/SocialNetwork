from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from typing import List
from pymongo import MongoClient, ASCENDING
from bson.objectid import ObjectId
import os

from models import Message, MessageInDB

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://user_service:8000/login")
SECRET_KEY = "supersecret"
ALGORITHM = "HS256"

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "chat_db")
client = MongoClient(MONGODB_URL)
db = client[MONGO_DB_NAME]
messages_collection = db["messages"]

messages_collection.create_index([("sender", ASCENDING)])
messages_collection.create_index([("receiver", ASCENDING)])


def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/message", response_model=MessageInDB)
def send_message(msg: Message, user: str = Depends(get_current_user)):
    if user != msg.sender:
        raise HTTPException(status_code=403, detail="Sender mismatch")
    result = messages_collection.insert_one(msg.dict())
    return MessageInDB(id=str(result.inserted_id), **msg.dict())


@app.get("/messages", response_model=List[MessageInDB])
def get_messages(user: str = Depends(get_current_user)):
    query = {"$or": [{"sender": user}, {"receiver": user}]}
    msgs = messages_collection.find(query)
    return [MessageInDB(id=str(m["_id"]), sender=m["sender"], receiver=m["receiver"], content=m["content"]) for m in msgs]


@app.get("/message/{msg_id}", response_model=MessageInDB)
def get_message_by_id(msg_id: str, user: str = Depends(get_current_user)):
    msg = messages_collection.find_one({"_id": ObjectId(msg_id)})
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if user != msg["sender"] and user != msg["receiver"]:
        raise HTTPException(status_code=403, detail="Access denied")
    return MessageInDB(id=str(msg["_id"]), sender=msg["sender"], receiver=msg["receiver"], content=msg["content"])


@app.delete("/message/{msg_id}")
def delete_message(msg_id: str, user: str = Depends(get_current_user)):
    msg = messages_collection.find_one({"_id": ObjectId(msg_id)})
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if user != msg["sender"]:
        raise HTTPException(status_code=403, detail="Only sender can delete")
    messages_collection.delete_one({"_id": ObjectId(msg_id)})
    return {"msg": "Message deleted"}
