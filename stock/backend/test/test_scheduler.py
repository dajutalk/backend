import requests
import time
import json

def test_scheduler_api(host="localhost", port="8000"):
    """스케줄러 API 테스트"""
    base_url = f"http://{host}:{port}/api/stocks"
    
    print("🧪 스케줄러 API 테스트 시작")
    print("=" * 60)
    
    # 1. 스케줄러 상태 확인
    print("\n1️⃣ 스케줄러 상태 확인")
    try:
        response = requests.get(f"{base_url}/scheduler/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 상태: {json.dumps(data, indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ 상태 확인 실패: {response.status_code}")
    except Exception as e:
        print(f"💥 오류: {e}")
    
    # 2. 모니터링 심볼 목록 확인
    print("\n2️⃣ 모니터링 심볼 목록 확인")
    try:
        response = requests.get(f"{base_url}/scheduler/symbols")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 총 {data['total']}개 심볼 모니터링 중")
            print(f"📋 처음 10개: {data['symbols'][:10]}")
        else:
            print(f"❌ 심볼 목록 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"💥 오류: {e}")
    
    # 3. 저장된 심볼 확인
    print("\n3️⃣ 저장된 심볼 확인")
    try:
        response = requests.get(f"{base_url}/symbols")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 데이터베이스에 {data['total']}개 심볼 저장됨")
            if data['symbols']:
                print(f"📋 일부 심볼: {data['symbols'][:10]}")
        else:
            print(f"❌ 저장된 심볼 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"💥 오류: {e}")
    
    # 4. 특정 심볼의 통계 확인 (AAPL)
    print("\n4️⃣ AAPL 통계 확인")
    try:
        response = requests.get(f"{base_url}/statistics/AAPL")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ AAPL 통계:")
            print(f"   💰 최신 가격: ${data.get('latest_price', 0):.2f}")
            print(f"   📊 총 레코드: {data.get('total_records', 0)}개")
            print(f"   📈 최고가: ${data.get('highest_price', 0):.2f}")
            print(f"   📉 최저가: ${data.get('lowest_price', 0):.2f}")
        else:
            print(f"❌ AAPL 통계 조회 실패: {response.status_code}")
    except Exception as e:
        print(f"💥 오류: {e}")
    
    print("\n" + "=" * 60)
    print("🧪 테스트 완료")

if __name__ == "__main__":
    test_scheduler_api()
