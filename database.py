from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
from models.user import Base

load_dotenv()

# Configurar el engine
# engine = create_engine(os.environ.get("DATABASE_URL"))
engine = create_engine("postgresql://ingenierichatuser:vitto123@localhost/ingenierichat", connect_args={'options': '-csearch_path=ingenierichat_schema'})
# Crear una fábrica de sesiones
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Crear las tablas
def create_tables():
    Base.metadata.create_all(bind=engine)

# Llamar a esta función al iniciar la aplicación
create_tables()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        