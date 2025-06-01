from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: EmailStr
    nickname: str
    provider: Optional[str] = "local"

class UserCreate(UserBase):
    password: Optional[str] = None

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: Optional[int] = None
    nickname: Optional[str] = None

class TokenData(BaseModel):
    username: Optional[str] = None
