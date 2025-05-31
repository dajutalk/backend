import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

# 로거 설정
logger = logging.getLogger(__name__)

# .env 파일 로드
load_dotenv()

# 환경변수 읽기
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "36367")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "stock_db")

# MySQL 8.0 호환성을 위한 연결 URL - charset만 지정
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# SQLAlchemy 엔진 설정 - connect_args 단순화
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 연결 상태 확인
    pool_recycle=3600,   # 1시간마다 연결 재생성
    echo=False,          # SQL 쿼리 로그 (디버깅용)
    connect_args={
        "charset": "utf8mb4"
    }
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# FastAPI에서 사용할 DB 세션 의존성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_db_and_tables():
    """데이터베이스와 테이블 생성 함수"""
    try:
        # 먼저 데이터베이스가 존재하는지 확인
        base_url = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}?charset=utf8mb4"
        temp_engine = create_engine(base_url, connect_args={"charset": "utf8mb4"})
        
        with temp_engine.begin() as connection:  # autocommit을 위해 begin() 사용
            # 데이터베이스 생성 (존재하지 않는 경우)
            connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
            logger.info(f"✅ 데이터베이스 '{DB_NAME}' 확인/생성 완료")
        
        temp_engine.dispose()
        
        # 모델들을 import해서 테이블 정의를 로드
        try:
            from stock.backend.models import StockQuote, CryptoQuote
            logger.info("✅ 모델 import 성공")
        except ImportError as e:
            logger.warning(f"⚠️ 모델 import 실패: {e}")
        
        # 모든 테이블 생성
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 모든 테이블 생성 완료")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스/테이블 생성 실패: {e}")
        import traceback
        logger.error(f"❌ 상세 오류:\n{traceback.format_exc()}")
        return False

def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("✅ 데이터베이스 연결 테스트 성공")
            return True
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        import traceback
        logger.error(f"❌ 상세 오류:\n{traceback.format_exc()}")
        return False
