from fastapi import FastAPI
from .database import create_db_and_tables
from .routers import auth, projects

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(auth.router)
app.include_router(projects.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Comprehensible Input Crowdfunding API"}
