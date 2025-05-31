from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..core.config import db_settings
from ..core.exceptions import DatabaseException
import logging
import time

logger = logging.getLogger(__name__)

# SQLAlchemy 설정
try:
    engine = create_engine(
        db_settings.url,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False,
        connect_args={"charset": "utf8mb4"}
    )
    logger.info("✅ 데이터베이스 엔진 생성 완료")
except Exception as e:
    logger.error(f"❌ 데이터베이스 엔진 생성 실패: {e}")
    raise DatabaseException("데이터베이스 엔진 생성 실패", e)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

def get_db():
    """FastAPI 의존성: DB 세션 제공"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection() -> bool:
    """데이터베이스 연결 테스트"""
    try:
        logger.info("🔍 데이터베이스 연결 테스트 시작...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("✅ 데이터베이스 연결 테스트 성공")
            return True
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        return False

def create_db_and_tables() -> bool:
    """데이터베이스와 테이블 생성"""
    try:
        logger.info("🔍 데이터베이스 생성 시작...")
        
        # 먼저 연결 테스트
        if not test_connection():
            # 데이터베이스가 없을 수도 있으므로 기본 연결로 시도
            logger.info("🔄 기본 연결로 데이터베이스 생성 시도...")
            temp_engine = create_engine(
                db_settings.base_url, 
                connect_args={"charset": "utf8mb4"}
            )
            
            try:
                with temp_engine.begin() as connection:
                    connection.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_settings.name}"))
                    logger.info(f"✅ 데이터베이스 '{db_settings.name}' 생성 완료")
                temp_engine.dispose()
                
                # 잠시 대기 후 다시 연결 테스트
                time.sleep(1)
                if not test_connection():
                    raise DatabaseException("데이터베이스 생성 후에도 연결 실패")
                    
            except Exception as e:
                logger.error(f"❌ 데이터베이스 생성 실패: {e}")
                temp_engine.dispose()
                raise
        
        # 모델 import 및 테이블 생성
        try:
            from .models import StockQuote, CryptoQuote
            logger.info("✅ 모델 import 성공")
        except ImportError as e:
            logger.warning(f"⚠️ 모델 import 실패: {e}")
        
        Base.metadata.create_all(bind=engine)
        logger.info("✅ 모든 테이블 생성 완료")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스/테이블 생성 실패: {e}")
        # 개발 환경에서는 계속 진행하도록 경고만 출력
        logger.warning("⚠️ 데이터베이스 설정에 문제가 있지만 애플리케이션을 계속 시작합니다.")
        logger.warning("⚠️ 데이터베이스 기능이 제한될 수 있습니다.")
        return False

def create_db_and_tables_safe():
    """안전한 데이터베이스 생성 (실패해도 애플리케이션 계속)"""
    try:
        return create_db_and_tables()
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
        logger.warning("⚠️ 데이터베이스 없이 애플리케이션을 시작합니다.")
        return False
