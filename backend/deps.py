from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from sqlmodel import Session

from .database import get_session
from .models import User
from .security import ALGORITHM, SECRET_KEY

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl="/auth/token"
)

class TokenPayload(BaseModel):
    sub: Optional[str] = None

def get_current_user(
    token: str = Depends(reusable_oauth2),
    session: Session = Depends(get_session)
) -> User:
    try:
        payload = jwt.decode(
            token, SECRET_KEY, algorithms=[ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        if not token_data.sub:
            raise ValueError("No subject in token")
        user_id = int(token_data.sub)
    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )
    
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
