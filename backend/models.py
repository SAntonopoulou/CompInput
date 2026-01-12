from typing import Optional
from sqlmodel import Field, SQLModel

class ItemBase(SQLModel):
    name: str
    description: Optional[str] = None
    price: float

class Item(ItemBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class ItemCreate(ItemBase):
    pass
