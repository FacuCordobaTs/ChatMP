from fastapi import FastAPI, APIRouter, Depends, HTTPException, Response, Cookie
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from pydantic import BaseModel
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv
from database import get_db
from models.user import User
from models.chat import ChatMessage

load_dotenv()

# FastAPI app initialization
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust for your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT configuration
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your_jwt_secret_key")  # Replace with your actual secret key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Helper function to create a JWT token
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Dependency to get the current user from the access token
async def get_current_user(access_token: str = Cookie(None), db: Session = Depends(get_db)):
    print("Inside get_current_user")
    print(f"Access token: {access_token}")
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not access_token:
        raise credentials_exception
    try:
        token = access_token.split()[1]  # Strip "Bearer" prefix
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

# Pydantic schema for incoming data
class TokenSchema(BaseModel):
    token: str

class MessageSchema(BaseModel):
    message: str

# Auth-related routes
@app.post("/auth/google/login")
async def auth_google(token: TokenSchema, response: Response, db: Session = Depends(get_db)):
    try:
        google_response = requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={token.token}"
        )
        if google_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        user_info = google_response.json()
        google_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name")
        picture = user_info.get("picture")

        if not google_id or not email:
            raise HTTPException(status_code=400, detail="Invalid user info")

        # Check if the user exists in the database
        user = db.query(User).filter(User.google_id == google_id).first()
        if user:
            user.email = email
            user.name = name
            user.picture = picture
        else:
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture,
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)

        # Create JWT token
        access_token = create_access_token(
            data={"sub": user.email}
        )

        # Set the access_token as an HttpOnly cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=1800,
            expires=1800,
            samesite="none",
            secure=True  # Use True for HTTPS environments
        )

        return {"status": "Login successful", "user": email}

    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@app.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

@app.post("/auth/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    print("Current User: ", current_user)
    return current_user

# Chat-related routes
@app.post("/chat/")
async def chat(message: MessageSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    print("Message: ", message)
    print("Current User in Chat: ", current_user)
    return {"message": message}

# Protected route example
@app.get("/auth/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": "This is a protected route", "user": current_user.email}
