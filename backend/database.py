import os
from sqlmodel import SQLModel, create_engine, Session

sqlite_file_name = "database.db"
default_db_url = f"sqlite:///{sqlite_file_name}"
database_url = os.environ.get("DATABASE_URL", default_db_url)

# Only use check_same_thread for SQLite
connect_args = {"check_same_thread": False} if "sqlite" in database_url else {}

engine = create_engine(database_url, echo=False, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
