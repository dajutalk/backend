# database.py
# DB 접속 설정 파일

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# .env 파일 로드
load_dotenv()

# 환경변수 읽기
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

# DB 접속 URL 조합
DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy 세팅
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# FastAPI에서 사용할 DB 세션 의존성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db  # 라우터 함수에게 db 세션 넘김
    finally:
        db.close()  # 요청 끝나면 자동으로 닫힘
'''
get_db(): DB 세션을 한 요청마다 열고 닫기 위해 만든 함수
의존성 주입: 방금 요청을 FastAPI가 자동으로 실행해 주는 구조

Depends(get_db): FastAPI가 이 함수 먼저 실행해서 결과를 자동으로 db에 넣음, 이렇게 쓰임
'''        