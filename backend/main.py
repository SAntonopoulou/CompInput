from typing import List
from fastapi import FastAPI, Depends
from sqlmodel import Session, select
from .database import create_db_and_tables, get_session
from .models import Item, ItemCreate

app = FastAPI()

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/items/", response_model=Item)
def create_item(item: ItemCreate, session: Session = Depends(get_session)):
    db_item = Item.from_orm(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

@app.get("/items/", response_model=List[Item])
def read_items(session: Session = Depends(get_session)):
    items = session.exec(select(Item)).all()
    return items

@app.get("/")
def read_root():
    return {"Hello": "World"}
