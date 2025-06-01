from fastapi import Depends, Cookie, HTTPException
from sqlalchemy.orm import Session
from stock.backend.database import get_db
from stock.backend.auth.auth_service import extract_user_id
from stock.backend.auth import crud
import logging

logger = logging.getLogger(__name__)

def get_current_user(
    access_token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    """현재 로그인된 사용자 조회"""
    if not access_token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")

    try:
        user_id = extract_user_id(access_token)
        user = crud.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        return user
    except Exception as e:
        logger.error(f"사용자 인증 실패: {e}")
        raise HTTPException(status_code=401, detail="토큰 검증 실패")

def get_current_user_optional(
    access_token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    """선택적 사용자 인증 (로그인하지 않아도 OK)"""
    if not access_token:
        return None
    
    try:
        user_id = extract_user_id(access_token)
        user = crud.get_user(db, user_id)
        return user
    except Exception:
        return None
