from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: str
    nickname: str
    provider: Optional[str] = "local"

class UserCreate(UserBase):
    password: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v, values):
        # 로컬 회원가입인 경우만 비밀번호 필요
        if values.get("provider") == "local":
            if v is None or len(v) < 6:
                raise ValueError('비밀번호는 6자리 이상이어야 합니다')
        return v
    
    @validator('nickname')
    def validate_nickname(cls, v):
        if len(v) < 2:
            raise ValueError('닉네임은 2자리 이상이어야 합니다')
        if len(v) > 20:
            raise ValueError('닉네임은 20자리 이하여야 합니다')
        return v

class UserUpdate(BaseModel):
    nickname: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('password')
    def validate_password(cls, v):
        if v is not None and len(v) < 6:
            raise ValueError('비밀번호는 6자리 이상이어야 합니다')
        return v

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

class EmailCheck(BaseModel):
    email: EmailStr
    available: bool
    message: str

class NicknameCheck(BaseModel):
    nickname: str
    available: bool
    message: str
