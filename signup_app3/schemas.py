# schemas.py
# 요청/응답 데이터 검증 파일

from pydantic import BaseModel
from typing import Optional  # password 구조 정의 시 Optional을 사용한 전통적 타입 힌트 방법 사용


# 회원 생성/로그인 시 사용하는 데이터 구조 정의
class UserCreate(BaseModel):
    email: str  # 일반 로그인은 실제 이메일, 카카오는 난수
    password: Optional[str] = None  # 일반 로그인은 입력, 카카오 로그인은 None
    nickname: str  # 일반 로그인은 사용자가 입력, 카카오는 프로필 닉네임 가져옴
    provider: str = "local"  # "local" 또는 "kakao" 구분용, local이 기본값

# 로그인 성공 시 클라이언트에게 보내는 토큰 데이터 구조
class Token(BaseModel):
    access_token: str  # 로그인 성공 후 발급하는 JWT 토큰 문자열
    token_type: str  # "bearer" 같은 토큰 타입 지정용 (보통 "bearer" 고정)