from fastapi import APIRouter, Depends, HTTPException, Form, Request, Response
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from stock.backend.database import get_db
from stock.backend.auth.auth_service import create_access_token
from stock.backend.auth.dependencies import get_current_user
from stock.backend.auth.kakao_service import get_kakao_access_token, get_kakao_user_info
from stock.backend.auth import models, schemas, crud
import os
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 환경변수
KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI", "http://localhost:8000/auth/kakao/callback")

@router.post("/login", response_model=schemas.Token)
def login_or_signup(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    nickname: str = Form(...),
    db: Session = Depends(get_db),
):
    """일반 로그인 또는 자동 회원가입"""
    user = crud.get_user_by_email(db, email)

    if user:
        # 기존 사용자 로그인
        if not user.password or not crud.verify_password(password, user.password):
            raise HTTPException(status_code=400, detail="잘못된 로그인 정보입니다")
        logger.info(f"기존 사용자 로그인: {email}")
    else:
        # 새 사용자 회원가입
        new_user = schemas.UserCreate(
            email=email,
            password=password,
            nickname=nickname,
            provider="local"
        )
        user = crud.create_user(db, new_user)
        logger.info(f"새 사용자 회원가입: {email}")

    # JWT 토큰 생성
    token = create_access_token(data={"sub": str(user.id)})

    # 쿠키 설정
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,  # 개발환경에서는 False
        samesite="lax",
        max_age=86400  # 24시간
    )
    
    return {"access_token": token, "token_type": "bearer", "user_id": user.id, "nickname": user.nickname}

@router.post("/kakao/callback", response_model=schemas.Token)
def kakao_login(
    response: Response,
    code: str = Form(...),
    db: Session = Depends(get_db)
):
    """카카오 로그인 콜백 처리"""
    try:
        # 카카오 액세스 토큰 발급
        kakao_access_token = get_kakao_access_token(code)
        if not kakao_access_token:
            raise HTTPException(status_code=400, detail="카카오 토큰 발급 실패")

        # 사용자 정보 조회
        user_info = get_kakao_user_info(kakao_access_token)
        if not user_info:
            raise HTTPException(status_code=400, detail="카카오 사용자 정보 조회 실패")

        kakao_id = str(user_info["id"])
        nickname = user_info["properties"]["nickname"]
        generated_email = f"kakao_{kakao_id}@kakao.local"

        # 사용자 조회 또는 생성
        user = crud.get_user_by_email(db, generated_email)
        if not user:
            new_user = schemas.UserCreate(
                email=generated_email,
                password=None,
                nickname=nickname,
                provider="kakao"
            )
            user = crud.create_user(db, new_user)
            logger.info(f"카카오 신규 사용자: {nickname}")
        else:
            logger.info(f"카카오 기존 사용자: {nickname}")

        # JWT 토큰 생성
        token = create_access_token(data={"sub": str(user.id)})
        
        # 쿠키 설정
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=86400
        )
        
        return {"access_token": token, "token_type": "bearer", "user_id": user.id, "nickname": user.nickname}
        
    except Exception as e:
        logger.error(f"카카오 로그인 처리 오류: {e}")
        raise HTTPException(status_code=500, detail="카카오 로그인 처리 중 오류가 발생했습니다")

@router.get("/kakao/callback")
def kakao_login_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """카카오 로그인 GET 콜백 (리다이렉트용)"""
    code = request.query_params.get("code")
    if not code:
        return RedirectResponse(url="http://localhost:3000?error=no_code")

    try:
        # 카카오 로그인 처리
        kakao_access_token = get_kakao_access_token(code)
        user_info = get_kakao_user_info(kakao_access_token)
        
        kakao_id = str(user_info["id"])
        nickname = user_info["properties"]["nickname"]
        generated_email = f"kakao_{kakao_id}@kakao.local"

        user = crud.get_user_by_email(db, generated_email)
        if not user:
            new_user = schemas.UserCreate(
                email=generated_email,
                password=None,
                nickname=nickname,
                provider="kakao"
            )
            user = crud.create_user(db, new_user)

        # JWT 토큰 생성
        token = create_access_token(data={"sub": str(user.id)})
        
        # 프론트엔드로 리다이렉트
        response = RedirectResponse(url="http://localhost:3000?login=success")
        response.set_cookie(
            key="access_token",
            value=token,
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=86400
        )
        
        return response
        
    except Exception as e:
        logger.error(f"카카오 콜백 처리 오류: {e}")
        return RedirectResponse(url="http://localhost:3000?error=kakao_failed")

@router.get("/me", response_model=schemas.User)
def read_me(current_user=Depends(get_current_user)):
    """현재 로그인된 사용자 정보"""
    return current_user

@router.post("/logout")
def logout(response: Response):
    """로그아웃"""
    response.delete_cookie(key="access_token")
    return {"message": "로그아웃 완료"}

@router.get("/kakao/redirect")
def redirect_to_kakao():
    """카카오 로그인 리다이렉트"""
    if not KAKAO_CLIENT_ID:
        raise HTTPException(status_code=500, detail="카카오 클라이언트 ID가 설정되지 않았습니다")
    
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?response_type=code"
        f"&client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
    )
    return RedirectResponse(kakao_auth_url)

@router.get("/status")
def auth_status():
    """인증 시스템 상태 확인"""
    return {
        "service": "auth",
        "status": "active",
        "kakao_configured": bool(KAKAO_CLIENT_ID),
        "jwt_configured": True
    }
