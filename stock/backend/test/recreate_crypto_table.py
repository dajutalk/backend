import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from stock.backend.database import engine
from stock.backend.models import Base, CryptoQuote
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_crypto_table():
    """암호화폐 테이블 완전 재생성"""
    try:
        with engine.connect() as connection:
            # 기존 테이블 삭제
            connection.execute("DROP TABLE IF EXISTS crypto_quotes")
            connection.commit()
            logger.info("🗑️ 기존 crypto_quotes 테이블 삭제됨")
            
        # 새 테이블 생성
        CryptoQuote.__table__.create(bind=engine)
        logger.info("✅ crypto_quotes 테이블 재생성 완료 (BIGINT 타임스탬프)")
        
        # 테이블 구조 확인
        with engine.connect() as connection:
            result = connection.execute("DESCRIBE crypto_quotes")
            print("\n📊 새 테이블 구조:")
            for row in result:
                print(f"   {row[0]}: {row[1]} {row[2] if row[2] == 'NO' else ''}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ crypto_quotes 테이블 재생성 실패: {e}")
        return False

if __name__ == "__main__":
    print("🔧 암호화폐 테이블 재생성 시작...")
    
    if recreate_crypto_table():
        print("✅ 테이블 재생성 성공!")
        print("🚀 이제 서버를 재시작하세요.")
    else:
        print("❌ 테이블 재생성 실패!")
