# models.py
# 일반/카카오 로그인을 모두 지원하는 통합 유저 테이블임

from sqlalchemy import Column, Integer, String
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True) # 1, 2, 3, 4... 이렇게 찍힘

    # 일반 로그인: 유저가 입력한 실제 이메일, 아이디로 취급함
    # 카카오 로그인: kakao_id = 329423 <- 이렇게 난수로 입력되는데, 이걸 이 필드에 넣음
    email = Column(String(100), unique=False, index=True, nullable=True)

    # 일반 로그인: 유저가 입력한 비밀번호 (bcrypt 사용)
    # 카카오 로그인: null값으로 db에 넣기
    password = Column(String(255), nullable=True)  # null값 넣을 때를 대비하여 nullable=True로 작성!!

    # 일반 로그인: 회원가입 시 유저가 입력
    # 카카오 로그인: 카카오 profile_nickname로 입력 (카카오에서 이것만 제공해 줌)
    nickname = Column(String(50), nullable=False, default="noname")

    # 일반 로그인: 'local'
    # 카카오 로그인: 'kakao'
    provider = Column(String(50), nullable=False)

