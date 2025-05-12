# crud.py
# DB 조회, 생성, 암호화/검증 파일

from sqlalchemy.orm import Session  # Session은 DB와 통신하는 SQLAlchemy의 객체이고 DB 작업(추가, 검색, 수정, 삭제)은 항상 Session 객체를 통해서 함
from passlib.context import CryptContext  # passlib 라이브러리를 사용해서 bcrypt 알고리즘으로 비밀번호를 암호화하고 비교
from . import models, schemas

# 비밀번호를 암호화하고 검증할 때 사용할 암호화 컨텍스트 설정
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# DB에서 email로 유저를 찾는 함수
'''
로그인, 회원가입 등에서 이 이메일로 이미 가입했는지 확인할 때 쓰는 용도
email은 사용자 입력이기 때문에 인증 전 상태에서 주로 사용
'''
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

# DB에서 user_id로 유저를 찾는 함수
'''
이미 로그인된 사용자 식별 시 사용
쿠키에 있는 JWT 토큰 안의 user ID를 기준으로 유저를 찾는 용도(sub 필드 -> user_id -> DB에서 유저 조회)
'''
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

# 새로운 유저를 DB에 추가하는 함수
def create_user(db: Session, user: schemas.UserCreate):
    # 비밀번호가 있는 경우 암호화해서 저장 (카카오 로그인은 password=None이라서 이 줄은 그냥 None 처리됨)
    hashed_password = pwd_context.hash(user.password) if user.password else None

    # 새로운 User 객체 생성 (DB 테이블과 매칭됨)
    db_user = models.User(
        email=user.email,
        password=hashed_password,  # 암호화된 비밀번호 저장
        nickname=user.nickname,
        provider=user.provider      # "local" 또는 "kakao"
    )

    # 세션에 추가하고 커밋해서 DB에 저장
    db.add(db_user)
    db.commit()

    # 방금 추가한 db_user 객체를 다시 새로고침 (id값 등 자동 생성된 필드 반영)
    db.refresh(db_user)

    # 최종 생성된 유저 객체를 반환
    return db_user


# 사용자가 입력한 비밀번호와 저장된 해시 비밀번호가 일치하는지 확인하는 함수
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)
