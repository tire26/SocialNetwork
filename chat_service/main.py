from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from typing import List

from models import Message

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="http://user_service:8000/login")

SECRET_KEY = "supersecret"
ALGORITHM = "HS256"

# In-memory store for messages
messages: List[Message] = []

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/message")
def send_message(msg: Message, user: str = Depends(get_current_user)):
    if user != msg.sender:
        raise HTTPException(status_code=403, detail="Sender mismatch")
    messages.append(msg)
    return {"msg": "Message sent"}

@app.get("/messages", response_model=List[Message])
def get_messages(user: str = Depends(get_current_user)):
    return [msg for msg in messages if msg.receiver == user or msg.sender == user]
