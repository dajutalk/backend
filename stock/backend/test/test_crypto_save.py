import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.crypto_service import crypto_service
from database import test_connection, create_db_and_tables
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_crypto_save():
    """암호화폐 저장 테스트"""
    print("🧪 암호화폐 저장 테스트 시작")
    print("=" * 60)
    
    # 1. 데이터베이스 연결 테스트
    print("\n1️⃣ 데이터베이스 연결 테스트")
    if test_connection():
        print("✅ 데이터베이스 연결 성공")
    else:
        print("❌ 데이터베이스 연결 실패")
        return
    
    # 2. 테이블 생성 확인
    print("\n2️⃣ 테이블 생성 확인")
    if create_db_and_tables():
        print("✅ 테이블 생성/확인 성공")
    else:
        print("❌ 테이블 생성 실패")
        return
    
    # 3. 테스트 데이터 생성
    print("\n3️⃣ 테스트 데이터 저장")
    test_crypto_data = {
        "symbol": "BTC",
        "s": "BINANCE:BTCUSDT",
        "p": "45000.50",
        "v": "1234567.89",
        "t": 1640995200000
    }
    
    print(f"📊 테스트 데이터: {test_crypto_data}")
    
    # 4. 저장 시도
    result = crypto_service.save_crypto_quote(test_crypto_data)
    
    if result:
        print("✅ 암호화폐 데이터 저장 성공!")
    else:
        print("❌ 암호화폐 데이터 저장 실패!")
    
    # 5. 저장된 데이터 조회
    print("\n4️⃣ 저장된 데이터 조회")
    latest = crypto_service.get_latest_crypto_quote("BTC")
    if latest:
        print(f"✅ 최신 데이터 조회 성공:")
        print(f"   ID: {latest.id}")
        print(f"   Symbol: {latest.symbol}")
        print(f"   S: {latest.s}")
        print(f"   P: {latest.p}")
        print(f"   V: {latest.v}")
        print(f"   T: {latest.t}")
        print(f"   Created: {latest.created_at}")
    else:
        print("❌ 저장된 데이터 조회 실패")
    
    print("\n" + "=" * 60)
    print("🧪 테스트 완료")

if __name__ == "__main__":
    test_crypto_save()
