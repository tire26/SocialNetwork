import json
import os
from datetime import datetime, timedelta

import psycopg2
import redis
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import jwt, JWTError
from passlib.context import CryptContext

from models import User, TokenResponse

app = FastAPI()

SECRET_KEY = "supersecret"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db:5432/users_db")
conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

redis_client = redis.Redis(host='redis', port=6379, decode_responses=True)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def get_password_hash(password):
    return pwd_context.hash(password)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def authenticate_user(username: str, password: str):
    cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    if not result:
        return None
    hashed_password = result[0]
    if not verify_password(password, hashed_password):
        return None
    return User(username=username, password=hashed_password)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return await get_user_by_username(username)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")


@app.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    token = create_access_token(data={"sub": user.username})
    return TokenResponse(access_token=token, token_type="bearer")


@app.post("/register")
async def register(user: User):
    cursor.execute("SELECT id FROM users WHERE username = %s", (user.username,))
    if cursor.fetchone():
        raise HTTPException(status_code=400, detail="User already exists")
    hashed_password = get_password_hash(user.password)
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (user.username, hashed_password))
    conn.commit()
    redis_client.set(f"user:{user.username}", json.dumps({"username": user.username, "password": hashed_password}), ex=60)
    return {"msg": "User registered"}


@app.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get("/user/{username}", response_model=User)
async def get_user_by_username(username: str):
    cache_key = f"user:{username}"

    cached_user = redis_client.get(cache_key)
    if cached_user:
        return User(**json.loads(cached_user))

    cursor.execute("SELECT username, password FROM users WHERE username = %s", (username,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="User not found")

    user_data = {"username": result[0], "password": result[1]}

    redis_client.set(cache_key, json.dumps(user_data), ex=60)

    return User(**user_data)