# main.py 
# FastAPI 엔트리포인트, API 라우팅

from fastapi import Response
from fastapi import FastAPI, Depends, HTTPException, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from . import models, schemas, crud, database, database, auth, kakao
from .dependencies import get_current_user
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

# 데이터베이스의 테이블 생성 (models.py의 모든 테이블을 실제 DB에 반영)
models.Base.metadata.create_all(bind=database.engine)

# FastAPI 앱 객체 생성
app = FastAPI()

KAKAO_CLIENT_ID = os.getenv("KAKAO_CLIENT_ID")
REDIRECT_URI = os.getenv("KAKAO_REDIRECT_URI")

# DB 세션 연결 함수 (요청마다 새 세션 열고 요청 끝나면 닫기)
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# [일반 로그인 or 자동 회원가입] API
@app.post("/auth/login", response_model=schemas.Token)
def login_or_signup(
    response: Response,  # 기본값이 없는 인자는 앞에 위치해야 함
    email: str = Form(...),           # 사용자 이메일
    password: str = Form(...),         # 사용자 비밀번호
    nickname: str = Form(...),         # 사용자 닉네임
    db: Session = Depends(get_db),      # DB 세션 의존성 주입
):
    # 입력한 이메일로 유저 검색
    user = crud.get_user_by_email(db, email)

    if user:
        # 이미 존재하는 유저라면 비밀번호 검증
        if not user.password or not crud.verify_password(password, user.password):
            raise HTTPException(status_code=400, detail="Invalid credentials")
    else:
        # 존재하지 않는다면 새로운 유저를 생성 (회원가입)
        new_user = schemas.UserCreate(
            email=email,
            password=password,
            nickname=nickname,
            provider="local"  # 일반 로그인은 provider = local
        )
        user = crud.create_user(db, new_user)

    # 로그인 성공 또는 회원가입 완료 시 토큰 발급
    token = auth.create_access_token(data={"sub": str(user.id)})

    # JWT 토큰 발급 후, 쿠키로 설정하는 코드
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,     # 로컬에서는 반드시 False로 둬야 함, 배포 시에는 secure=True로 바꿔야 함
        samesite="lax"
    )
    return {"access_token": token, "token_type": "bearer"}


# [카카오 로그인] API

# [카카오 로그인] API
@app.post("/auth/kakao/callback", response_model=schemas.Token)
def kakao_login(
    code: str = Form(...),            # 프론트에서 받은 인가 코드 (authorization code)
    db: Session = Depends(get_db)     # DB 세션 의존성 주입
):
    # 인가 코드를 사용해 카카오 access_token 발급
    kakao_access_token = kakao.get_kakao_access_token(code)
    if not kakao_access_token:
        raise HTTPException(status_code=400, detail="카카오 토큰 발급 실패")

    # access_token으로 사용자 정보 조회
    user_info = kakao.get_kakao_user_info(kakao_access_token)
    if not user_info:
        raise HTTPException(status_code=400, detail="카카오 사용자 정보 실패")

    # 카카오 사용자 고유 ID (난수) 가져오기
    kakao_id = str(user_info["id"])

    # 카카오 프로필 닉네임 가져오기
    nickname = user_info["properties"]["nickname"]

    # 이메일 필드에 "kakao_난수" 형태로 저장
    generated_email = f"kakao_{kakao_id}"

    # 이메일로 기존 유저 찾기
    user = crud.get_user_by_email(db, generated_email)
    if not user:
        # 없으면 새로 가입 처리 (카카오는 password 없음)
        new_user = schemas.UserCreate(
            email=generated_email,
            password=None,
            nickname=nickname,
            provider="kakao"  # provider는 kakao로 설정
        )
        user = crud.create_user(db, new_user)

    # 로그인 성공 시 토큰 발급
    token = auth.create_access_token(data={"sub": str(user.id)})

    return {"access_token": token, "token_type": "bearer"}


@app.get("/auth/kakao/callback")
def kakao_login_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    code = request.query_params.get("code")  # ?code=xxxx
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    # 인가 코드를 사용해 카카오 access_token 발급
    kakao_access_token = kakao.get_kakao_access_token(code)
    if not kakao_access_token:
        raise HTTPException(status_code=400, detail="카카오 토큰 발급 실패")

    # access_token으로 사용자 정보 조회
    user_info = kakao.get_kakao_user_info(kakao_access_token)
    if not user_info:
        raise HTTPException(status_code=400, detail="카카오 사용자 정보 실패")

    # 카카오 사용자 고유 ID (난수) 가져오기
    kakao_id = str(user_info["id"])

    # 카카오 프로필 닉네임 가져오기
    nickname = user_info["properties"]["nickname"]

    # 이메일 필드에 "kakao_난수" 형태로 저장
    generated_email = f"kakao_{kakao_id}"

    # 이메일로 기존 유저 찾기
    user = crud.get_user_by_email(db, generated_email)
    if not user:
        # 없으면 새로 가입 처리 (카카오는 password 없음)
        new_user = schemas.UserCreate(
            email=generated_email,
            password=None,
            nickname=nickname,
            provider="kakao"  # provider는 kakao로 설정
        )
        user = crud.create_user(db, new_user)

    # 로그인 성공 시 토큰 발급
    token = auth.create_access_token(data={"sub": str(user.id)})

    response = RedirectResponse(url="http://localhost:3000")

    # 쿠키 붙이기
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=False,   # 운영 시 True
        samesite="lax"
    )

    return response
   
    # 로그인 성공한 사용자를 받아줄 특정 URL 페이지를 프론트에서 만들 건데,
    # 아직 주소가 안 정해졌으니 http://localhost:3000/kakao/success 로 임시 저장하겠음

# 쿠키에 access_token이 있고 유효하면 유저 정보를 반환하는 라우터
@app.get("/api/auth/kakao/callback")
def redirect_to_kakao():
    kakao_auth_url = (
        f"https://kauth.kakao.com/oauth/authorize"
        f"?response_type=code"
        f"&client_id={KAKAO_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
    )
    return RedirectResponse(kakao_auth_url)

# @app.get("/auth/kakao/callback")
# def kakao_login_callback(request: Request):
#     # 쿼리 파라미터에서 code 꺼내기
#     code = request.query_params.get("code")
    
#     # code가 있는지 확인해서 응답
#     if code:
#         return JSONResponse(content={"message": "카카오 콜백 테스트 성공", "code": code})
#     else:
#         return JSONResponse(content={"error": "code 파라미터가 없습니다"}, status_code=400)

@app.get("/auth/me", response_model=schemas.User)
def read_me(current_user=Depends(get_current_user)):
    return current_user    


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React 개발 서버 주소
    allow_credentials=True,
    allow_methods=["*"],                      # 모든 메서드 허용 (GET, POST 등)
    allow_headers=["*"],                      # 모든 헤더 허용
)