# dependencies.py
# 자주 쓰이는 인증/로그인 같은 공통 기능을 한 곳에 모아둔 (의존성)파일 작성
# 코드 중복 방지, 자동 실행(라우터에 Depends()만 붙이면 FastAPI가 알아서 실행함), 테스트 용이

from fastapi import Depends, Cookie, HTTPException
from sqlalchemy.orm import Session # SQLAlchemy 세션 -> DB 접근용
from . import auth, crud, database


# 라우터에서(main.py에서) Depends(get_current_user)로 쓰이게 될 함수
def get_current_user(
    access_token: str = Cookie(None), # 쿠키 이름이 access_token인 값을 자동으로 받아오고 없으면 None(로그인 안 한 상태) 처리
    db: Session = Depends(database.get_db) # DB 세션을 의존성으로 주입받음
):
    
    # 쿠키에 accss_token이 없으면 사용자가 로그인 안 했거나 쿠키가 만료됐다는 코드
    if not access_token:
        raise HTTPException(status_code=401, detail="로그인이 필요합니다")

    # 토큰에서 유저 ID 추출
    try:
        user_id = auth.extract_user_id(access_token) # extract_user_id() 함수는 토큰을 디코딩해서 sub 필드에서 user ID를 꺼냄(auth.py에 정의함)
        
        # 추출한 user_id로 DB에서 사용자 조회
        user = crud.get_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="토큰 검증 실패")
