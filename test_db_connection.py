from stock.backend.database import engine, SessionLocal, test_connection, create_db_and_tables
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def comprehensive_db_test():
    """포괄적인 데이터베이스 테스트"""
    try:
        # 1. 기본 연결 테스트
        logger.info("🔍 기본 연결 테스트 시작...")
        if not test_connection():
            logger.error("❌ 기본 연결 테스트 실패")
            return False
        
        # 2. 데이터베이스 및 테이블 생성 테스트
        logger.info("🔍 데이터베이스/테이블 생성 테스트 시작...")
        if not create_db_and_tables():
            logger.error("❌ 데이터베이스/테이블 생성 실패")
            return False
        
        # 3. 세션 테스트
        logger.info("🔍 세션 테스트 시작...")
        db = SessionLocal()
        try:
            result = db.execute(text("SELECT VERSION()"))
            version = result.fetchone()[0]
            logger.info(f"✅ MySQL 버전: {version}")
            
            # 테이블 목록 조회
            result = db.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            logger.info(f"✅ 생성된 테이블: {tables if tables else '테이블 없음 (모델 import 필요)'}")
            
        finally:
            db.close()
        
        logger.info("✅ 모든 데이터베이스 테스트 통과")
        return True
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 테스트 실패: {e}")
        print("⚠️ MySQL 서버가 실행 중인지, 포트/주소/비밀번호가 맞는지 확인하세요.")
        import traceback
        logger.error(f"❌ 상세 오류:\n{traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = comprehensive_db_test()
    if success:
        print("\n🎉 데이터베이스 설정이 완료되었습니다!")
    else:
        print("\n💥 데이터베이스 설정에 문제가 있습니다.")
