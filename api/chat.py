from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from openai import OpenAI
from models.chat import ChatMessage
from models.user import User
# from .auth import get_current_user
from database import get_db
from .auth import get_current_user

router = APIRouter()

# client = OpenAI()

class MessageSchema(BaseModel):
    message: str


@router.post("/")
async def chat(message: MessageSchema, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    print(message)
    print(current_user)
    
    return {"message": message}
    # try:
        # Guardar el mensaje del usuario en la base de datos
        # user_message = ChatMessage(user_id=current_user.id, role='user', content=message.message)
        # db.add(user_message)
        # db.commit()

        # # Enviar el mensaje a OpenAI
        # response = client.ChatCompletion.create(
        #     model="gpt-4o-mini",
        #     messages=[{"role": "user", "content": message.message}]
        # )

        # ai_message = response.choices[0].message['content']

        # # Guardar la respuesta de la IA en la base de datos
        # ai_chat_message = ChatMessage(user_id=current_user.id, role='assistant', content=ai_message)
        # db.add(ai_chat_message)
        # db.commit()

        # return {"message": ai_message}
    # return {"message": message}
    
    # except Exception as e:
    #     db.rollback()
    #     raise HTTPException(status_code=500, detail=str(e))

# @router.get("/chat/history")
# async def get_chat_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
#     messages = db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id).order_by(ChatMessage.timestamp).all()
#     return messages