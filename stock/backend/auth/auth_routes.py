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

@router.post("/signup", response_model=schemas.Token)
def signup(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    nickname: str = Form(...),
    db: Session = Depends(get_db),
):
    """일반 회원가입"""
    try:
        # 이메일 중복 확인
        existing_user = crud.get_user_by_email(db, email)
        if existing_user:
            raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다")

        # 비밀번호 강도 검증 (기본적인 검증)
        if len(password) < 6:
            raise HTTPException(status_code=400, detail="비밀번호는 6자리 이상이어야 합니다")

        # 닉네임 중복 확인
        existing_nickname = crud.get_user_by_nickname(db, nickname)
        if existing_nickname:
            raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다")

        # 새 사용자 생성
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
            secure=False,
            samesite="lax",
            max_age=86400
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "nickname": user.nickname
        }

    except HTTPException as http_exc:
        raise http_exc

    except Exception as e:
        logger.error("❌ 회원가입 중 서버 오류 발생:")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="회원가입 중 서버 오류가 발생했습니다.")
    
@router.post("/login", response_model=schemas.Token)
def login(
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """일반 로그인 (회원가입 분리됨)"""
    user = crud.get_user_by_email(db, email)
    
    if not user:
        raise HTTPException(status_code=404, detail="등록되지 않은 이메일입니다")
    
    # 비밀번호 확인
    if not user.password or not crud.verify_password(password, user.password):
        raise HTTPException(status_code=400, detail="잘못된 비밀번호입니다")
    
    # 계정 활성화 확인
    if not user.is_active:
        raise HTTPException(status_code=400, detail="비활성화된 계정입니다")
    
    logger.info(f"사용자 로그인: {email}")

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
            # 카카오 신규 사용자 자동 회원가입
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
        logger.warning("🔴 code 없음")
        return RedirectResponse(url="http://localhost:3000?error=no_code")

    try:
        logger.info("🔵 code 수신 완료, 토큰 요청 시작")
        kakao_access_token = get_kakao_access_token(code)
        logger.info(f"🟢 Kakao Access Token: {kakao_access_token}")

        user_info = get_kakao_user_info(kakao_access_token)
        logger.info(f"🟢 Kakao User Info: {user_info}")

        kakao_id = str(user_info["id"])
        nickname = user_info["properties"]["nickname"]
        generated_email = f"kakao_{kakao_id}@kakao.local"

        logger.info(f"🟡 사용자 이메일 생성: {generated_email}")

        user = crud.get_user_by_email(db, generated_email)
        if not user:
            logger.info(f"🟠 DB에 사용자 없음. 생성 시도.")
            new_user = schemas.UserCreate(
                email=generated_email,
                password=None,
                nickname=nickname,
                provider="kakao"
            )
            try:
                user = crud.create_user(db, new_user)
                logger.info(f"🟢 사용자 생성 완료: {user.email}")
            except Exception as e:
                logger.error("❌ 사용자 생성 중 오류 발생")
                logger.error(traceback.format_exc())
                return RedirectResponse(url="http://localhost:3000?error=creation_failed")

        # JWT 토큰 생성
        token = create_access_token(data={"sub": str(user.id)})
        logger.info(f"✅ JWT 생성 완료")

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
        logger.error(f"❌ 카카오 콜백 처리 오류: {e}")
        logger.error(traceback.format_exc())
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

@router.post("/check-email")
async def check_email_availability(
    email: str = Form(...),
    db: Session = Depends(get_db)
):
    """이메일 사용 가능 여부 확인"""
    try:
        existing_user = crud.get_user_by_email(db, email)
        available = existing_user is None
        
        return {
            "email": email,
            "available": available,
            "message": "사용 가능한 이메일입니다" if available else "이미 사용 중인 이메일입니다"
        }
    except Exception as e:
        logger.error(f"이메일 확인 오류: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="이메일 확인 중 오류가 발생했습니다")

@router.post("/check-nickname")
async def check_nickname_availability(
    nickname: str = Form(...),
    db: Session = Depends(get_db)
):
    """닉네임 사용 가능 여부 확인"""
    try:
        existing_user = crud.get_user_by_nickname(db, nickname)
        available = existing_user is None
        
        return {
            "nickname": nickname,
            "available": available,
            "message": "사용 가능한 닉네임입니다" if available else "이미 사용 중인 닉네임입니다"
        }
    except Exception as e:
        logger.error(f"닉네임 확인 오류: {e}")
        raise HTTPException(status_code=500, detail="닉네임 확인 중 오류가 발생했습니다")
