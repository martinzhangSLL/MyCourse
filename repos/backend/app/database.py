import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Get the directory where this file is located (app/)
APP_DIR = os.path.dirname(os.path.abspath(__file__))
# Go up two levels to reach repos/
REPOS_DIR = os.path.dirname(os.path.dirname(APP_DIR))
DATABASE_PATH = os.path.join(REPOS_DIR, "db", "scores.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass
