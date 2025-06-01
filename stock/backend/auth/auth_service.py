import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# 환경변수 로드
load_dotenv()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

def create_access_token(data: dict):
    """JWT 액세스 토큰 생성"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """토큰 검증 및 디코딩"""
    try:
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return decoded
    except JWTError as e:
        logger.error(f"토큰 검증 실패: {e}")
        raise

def extract_user_id(token: str) -> int:
    """토큰에서 사용자 ID 추출"""
    payload = verify_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("토큰에 user_id 없음")
    return int(user_id)
