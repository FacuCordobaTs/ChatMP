from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv
from models.user import User
from pydantic import BaseModel
from database import get_db

load_dotenv()

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configuración de JWT
SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class TokenSchema(BaseModel):
    token: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@router.post("/google/login")
async def auth_google(token: TokenSchema, response: Response, db: Session = Depends(get_db)):
    try:
        # Verificar el token con Google
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

        # Verificar si el usuario ya existe en la base de datos
        user = db.query(User).filter(User.google_id == google_id).first()
        if user:
            # Si el usuario ya existe, actualiza la información
            user.email = email
            user.name = name
            user.picture = picture
        else:
            # Si el usuario no existe, créalo
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture,
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)

        print(user)

        # Crear token JWT
        access_token = create_access_token(
            data={"sub": user.email}
        )

        # Establecer la cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=1800,
            expires=1800,
            samesite="none",
            secure=True  # set to True if using HTTPS
        )

        return {"status": "Login successful", "user": email}

    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

# Dependencia para obtener el usuario actual
async def get_current_user(access_token: str = Cookie(None), db: Session = Depends(get_db)):
    print(access_token)
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not access_token:
        raise credentials_exception
    try:
        print(access_token)
        token = access_token.split()[1]  # Elimina el prefijo "Bearer"
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

@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    print(current_user)
    return current_user

# Ejemplo de ruta protegida
@router.get("/protected")
async def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": "This is a protected route", "user": current_user.email}