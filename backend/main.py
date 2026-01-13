from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import create_db_and_tables
from .routers import auth, projects, pledges, videos, users, requests, notifications

app = FastAPI()

origins = [
    "http://localhost:5173", # Vite default
    "http://localhost:3000", # React default (alternative)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(pledges.router)
app.include_router(videos.router)
app.include_router(users.router)
app.include_router(requests.router)
app.include_router(notifications.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Comprehensible Input Crowdfunding API"}
