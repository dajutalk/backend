import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from stock.backend.models import Base
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# MySQL 데이터베이스 URL 설정
DATABASE_URL = os.getenv(
    "STOCK_DATABASE_URL", 
    "mysql+pymysql://stock_user:36367@localhost:3306/stock_db?charset=utf8mb4"
)

logger.info(f"데이터베이스 연결 URL: {DATABASE_URL}")

# SQLAlchemy 엔진 생성
try:
    engine = create_engine(
        DATABASE_URL,
        echo=True,  # SQL 쿼리 로그 출력
        pool_pre_ping=True,  # 연결 상태 확인
        pool_recycle=3600,   # 1시간마다 연결 갱신
    )
    logger.info("✅ 데이터베이스 엔진 생성 완료")
except Exception as e:
    logger.error(f"❌ 데이터베이스 엔진 생성 실패: {e}")
    raise

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """데이터베이스 세션 생성"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_db_and_tables():
    """데이터베이스 테이블 생성"""
    try:
        # 연결 테스트
        with engine.connect() as connection:
            logger.info("✅ 데이터베이스 연결 테스트 성공")
        
        # 테이블 생성
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 데이터베이스 테이블 생성 완료")
        return True
    except Exception as e:
        logger.error(f"❌ 데이터베이스 테이블 생성 실패: {e}")
        logger.error("💡 다음 명령어로 MySQL 사용자와 데이터베이스를 생성하세요:")
        logger.error("   mysql -u root -p")
        logger.error("   CREATE DATABASE stock_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        logger.error("   CREATE USER 'stock_user'@'localhost' IDENTIFIED BY '36367';")
        logger.error("   GRANT ALL PRIVILEGES ON stock_db.* TO 'stock_user'@'localhost';")
        logger.error("   FLUSH PRIVILEGES;")
        return False

def test_connection():
    """데이터베이스 연결 테스트"""
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            logger.info("✅ 데이터베이스 연결 테스트 성공")
            return True
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        return False
