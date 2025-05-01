# main.py 
# FastAPI 엔트리포인트, API 라우팅

from fastapi import FastAPI, Depends, HTTPException, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from . import models, schemas, crud, database, auth, kakao

# 데이터베이스의 테이블 생성 (models.py의 모든 테이블을 실제 DB에 반영)
models.Base.metadata.create_all(bind=database.engine)

# FastAPI 앱 객체 생성
app = FastAPI()

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
    email: str = Form(...),           # 사용자 이메일
    password: str = Form(...),         # 사용자 비밀번호
    nickname: str = Form(...),         # 사용자 닉네임
    db: Session = Depends(get_db)      # DB 세션 의존성 주입
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

    return {"access_token": token, "token_type": "bearer"}


# [카카오 로그인] API
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

    # 프론트로 토큰 넘겨주기, 실제 사용하는 프론트 주소 작성
    return RedirectResponse(url=f"http://localhost:3000/kakao/success?token={token}")
    '''
    로그인 성공한 사용자를 받아줄 특정 URL 페이지를 프론트에서 만들 건데,
    아직 주소가 안 정해졌으니 http://localhost:3000/kakao/success 로 임시 저장하겠음
    '''