# auth.py
# JWT 토큰 생성 파일

import os
from datetime import datetime, timedelta
from jose import jwt
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