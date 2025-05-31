import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import recreate_crypto_table, test_connection
import logging

logging.basicConfig(level=logging.INFO)

def fix_crypto_table():
    """암호화폐 테이블 타임스탬프 필드 수정"""
    print("🔧 암호화폐 테이블 수정 시작")
    print("=" * 60)
    
    # 1. 데이터베이스 연결 테스트
    print("\n1️⃣ 데이터베이스 연결 테스트")
    if not test_connection():
        print("❌ 데이터베이스 연결 실패")
        return
    print("✅ 데이터베이스 연결 성공")
    
    # 2. 기존 테이블 백업 (선택사항)
    print("\n2️⃣ 테이블 재생성")
    print("⚠️ 주의: 기존 crypto_quotes 테이블의 모든 데이터가 삭제됩니다!")
    
    confirm = input("계속하시겠습니까? (y/N): ")
    if confirm.lower() != 'y':
        print("❌ 작업이 취소되었습니다")
        return
    
    # 3. 테이블 재생성
    if recreate_crypto_table():
        print("✅ crypto_quotes 테이블 재생성 완료!")
        print("📊 새 테이블 구조:")
        print("   - symbol: VARCHAR(20)")
        print("   - s: VARCHAR(50)")
        print("   - p: VARCHAR(20)")
        print("   - v: VARCHAR(20)")
        print("   - t: BIGINT (타임스탬프, 밀리초 단위)")
        print("   - created_at: DATETIME")
        print("   - updated_at: DATETIME")
    else:
        print("❌ 테이블 재생성 실패")
    
    print("\n" + "=" * 60)
    print("🔧 작업 완료")

if __name__ == "__main__":
    fix_crypto_table()
