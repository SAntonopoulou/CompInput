import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from .database import create_db_and_tables, engine
from .routers import auth, projects, pledges, videos, users, requests, notifications, ratings, admin
from .models import User, UserRole
from .security import get_password_hash

app = FastAPI()

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
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
    
    # Create default admin if configured
    # Ensure ADMIN_EMAIL and ADMIN_PASSWORD are set in your environment variables
    admin_email = os.environ.get("ADMIN_EMAIL")
    admin_password = os.environ.get("ADMIN_PASSWORD")
    
    if admin_email and admin_password:
        with Session(engine) as session:
            statement = select(User).where(User.email == admin_email)
            existing_admin = session.exec(statement).first()
            
            if not existing_admin:
                admin_user = User(
                    email=admin_email,
                    hashed_password=get_password_hash(admin_password),
                    full_name="System Admin",
                    role=UserRole.ADMIN
                )
                session.add(admin_user)
                session.commit()
                print(f"Created default admin user: {admin_email}")
            else:
                print(f"Admin user {admin_email} already exists.")
    else:
        print("No ADMIN_EMAIL or ADMIN_PASSWORD set. Skipping default admin creation.")

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(pledges.router)
app.include_router(videos.router)
app.include_router(users.router)
app.include_router(requests.router)
app.include_router(notifications.router)
app.include_router(ratings.router)
app.include_router(admin.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Comprehensible Input Crowdfunding API"}
