from sqlalchemy.orm import Session
from stock.backend.auth import models, schemas
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """비밀번호 해시화"""
    return pwd_context.hash(password)

def get_user(db: Session, user_id: int):
    """사용자 ID로 조회"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str):
    """이메일로 사용자 조회"""
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    """새 사용자 생성"""
    hashed_password = None
    if user.password:
        hashed_password = get_password_hash(user.password)
    
    db_user = models.User(
        email=user.email,
        nickname=user.nickname,
        password=hashed_password,
        provider=user.provider
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
