from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base  # Assuming this is your declarative base

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))

    user = relationship("User", back_populates="messages")

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    picture = Column(String)

    messages = relationship("ChatMessage", back_populates="user")
