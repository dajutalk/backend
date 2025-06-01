from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from stock.backend.database.connection import Base

class User(Base):
    """사용자 모델"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    nickname = Column(String(100), nullable=False)
    password = Column(String(255), nullable=True)  # 카카오 로그인은 비밀번호 없음
    provider = Column(String(20), default="local")  # local, kakao 등
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', nickname='{self.nickname}')>"
