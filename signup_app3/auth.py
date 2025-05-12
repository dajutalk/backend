# auth.py
# JWT 토큰 생성 파일

import os
from datetime import datetime, timedelta
from jose import jwt, JWTError
from dotenv import load_dotenv

# .env 파일 불러오기(JWT 관련 코드 불러와야 하니까)
load_dotenv()

# .env 파일에서 환경변수 읽기
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")  # JWT를 암호화할 때 사용하는 비밀 키
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM")    # JWT 암호화 알고리즘 (보통 HS256)
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES"))  # 토큰 만료 시간 (분 단위)

# access_token 생성 함수: 주어진 data(dict)를 JWT access token으로 암호화해서 반환하는 함수
def create_access_token(data: dict):

    # 복사본 만들기 (원본 data 건드리지 않기 위해)
    to_encode = data.copy()

    # 토큰 만료 시간 설정 (현재 시간 + 설정한 만료 분)
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)

    # payload에 만료 시간 추가
    to_encode.update({"exp": expire})

    # JWT 토큰 생성 (payload, secret key, 알고리즘)
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

    return encoded_jwt


# 토큰이 유효한지 확인하고 디코딩된 payload 반환하는 함수
def verify_token(token: str):
    print("검증 중인 토큰:", token)
    print("사용된 키:", JWT_SECRET_KEY)
    print("사용된 알고리즘:", JWT_ALGORITHM)
    try:
        decoded = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        print("디코딩 성공:", decoded)
        return decoded
    except JWTError as e:
        print("디코딩 실패:", str(e))
        raise


# verify_token()으로 확인한 페이로드에서 sub을 꺼내 유저 ID로 반환하는 함수
def extract_user_id(token: str) -> int: # int형 사용자 ID 반환
    payload = verify_token(token)
    user_id = payload.get("sub") # sub은 이 토큰이 누구를 위한 것인지를 나타내는 필드이고, 이걸 user_id(유저 식별자)로 사용함
    if not user_id:
        raise ValueError("토큰에 user_id 없음")
    return int(user_id)    
# 위 user_id로 DB에서 유저 객체를 가져와 로그인 여부를 판단