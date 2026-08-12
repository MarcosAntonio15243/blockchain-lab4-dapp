from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config import settings

# Ex de DATABASE_URL no .env: "sqlite:///./banco.db" ou "postgresql://user:senha@host/db"
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()