import requests
import json
import time
import sys
import argparse
import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd

def get_stock_quote(symbol, host="localhost", port="8000"):
    """REST API를 통해 주식 시세 정보를 가져오는 함수"""
    url = f"http://{host}:{port}/api/stocks/quote?symbol={symbol}"
    print(f"🔗 API 요청: {url}")  # 요청 URL 로그
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API 응답 성공: {len(str(data))} bytes")  # 응답 크기 로그
            return data
        else:
            print(f"❌ API 요청 실패: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"💥 요청 중 오류 발생: {e}")
        return None

def print_quote_info(quote):
    """주식 시세 정보를 표준 출력으로 출력"""
    if not quote:
        print("데이터 없음")
        return
    
    # 디버깅: 전체 응답 데이터 출력
    print(f"\n🔍 전체 응답 데이터: {quote}")
    
    # 가격 정보 출력
    print(f"\n{'=' * 60}")
    print(f"심볼: {quote.get('symbol', 'N/A')}")
    print(f"타임스탬프: {quote.get('t', 0)}")
    print(f"현재 가격: ${quote.get('c', 0):.2f}")
    
    # 변동 정보
    change = quote.get('d', 0)
    change_percent = quote.get('dp', 0)
    change_symbol = "▲" if change >= 0 else "▼"
    change_color = "\033[92m" if change >= 0 else "\033[91m"  # 녹색 또는 빨간색
    print(f"변동: {change_color}{change_symbol} {abs(change):.2f} ({change_percent:.2f}%)\033[0m")
    
    # 기타 정보
    print(f"시가: ${quote.get('o', 0):.2f}")
    print(f"고가: ${quote.get('h', 0):.2f}")
    print(f"저가: ${quote.get('l', 0):.2f}")
    print(f"전일 종가: ${quote.get('pc', 0):.2f}")
    
    # 마지막 업데이트 시간
    if 'update_time' in quote:
        update_time = datetime.fromtimestamp(quote['update_time']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"최종 업데이트: {update_time}")
    
    # 데이터 소스 정보 출력 (강조 표시)
    data_source = quote.get('data_source')
    cache_age = quote.get('cache_age', 0)
    
    print(f"\n{'📊 데이터 소스 정보 📊':^60}")
    print("-" * 60)
    print(f"🔍 data_source 값: '{data_source}' (타입: {type(data_source)})")
    print(f"🔍 cache_age 값: {cache_age} (타입: {type(cache_age)})")
    
    if data_source == 'cache':
        print(f"📋 데이터 소스: \033[94m캐시에서 조회\033[0m")
        print(f"⏰ 캐시 경과시간: {cache_age:.1f}초")
        if cache_age < 30:
            print("✅ 신선한 캐시 데이터")
        elif cache_age < 60:
            print("⚡ 적당한 캐시 데이터")
        else:
            print("⚠️ 오래된 캐시 데이터")
    elif data_source == 'api':
        print(f"🌐 데이터 소스: \033[92mAPI 직접 호출\033[0m")
        print(f"🆕 새로운 데이터 (방금 업데이트됨)")
    elif data_source is None:
        print(f"⚠️ 데이터 소스: \033[93m정보 없음 (None)\033[0m")
        print(f"   🔧 백엔드에서 data_source 필드를 제공하지 않음")
        print(f"   🔧 백엔드 로그를 확인하여 수정이 필요함")
    else:
        print(f"❓ 데이터 소스: \033[91m{data_source}\033[0m (예상치 못한 값)")
    
    print(f"{'=' * 60}\n")

def create_real_time_plot(symbol, interval=5, duration=None, host="localhost", port="8000"):
    """지정된 간격으로 주식 시세를 가져와 실시간 그래프로 표시"""
    plt.figure(figsize=(12, 6))
    plt.title(f"{symbol} Real-time Stock Price")
    plt.xlabel("Time")
    plt.ylabel("Price ($)")
    plt.grid(True)
    
    # 데이터 저장용 (최대 100개 포인트로 제한)
    MAX_POINTS = 100
    times = []
    prices = []
    
    try:
        start_time = time.time()
        iteration = 0
        
        print(f"\n🚀 {symbol} 실시간 모니터링 시작")
        print(f"📡 서버: {host}:{port}")
        print(f"⏱️ 갱신 간격: {interval}초")
        print(f"{'=' * 80}")
        
        while True:
            # 주식 시세 데이터 요청
            quote = get_stock_quote(symbol, host, port)
            
            if quote:
                current_time = datetime.now().strftime('%H:%M:%S')
                price = quote.get('c', 0)
                
                # 데이터 추가 (최대 포인트 수 유지)
                times.append(current_time)
                prices.append(price)
                
                if len(times) > MAX_POINTS:
                    times.pop(0)
                    prices.pop(0)
                
                # 변동 정보
                change = quote.get('d', 0)
                change_percent = quote.get('dp', 0)
                change_symbol = "▲" if change >= 0 else "▼"
                
                # 데이터 소스 정보 가져오기
                data_source = quote.get('data_source')
                cache_age = quote.get('cache_age', 0)
                
                # 데이터 소스 아이콘과 텍스트 (더 자세히)
                if data_source == 'cache':
                    source_icon = "📋"
                    source_text = f"캐시({cache_age:.0f}s)"
                    source_color = "\033[94m"  # 파란색
                elif data_source == 'api':
                    source_icon = "🌐"
                    source_text = "API호출"
                    source_color = "\033[92m"  # 녹색
                elif data_source is None:
                    source_icon = "⚠️"
                    source_text = "정보없음"
                    source_color = "\033[93m"  # 노란색
                else:
                    source_icon = "❓"
                    source_text = str(data_source)
                    source_color = "\033[91m"  # 빨간색
                
                # 콘솔에 현재 정보 출력 (색상 포함)
                print(f"\r{source_icon} {symbol}: ${price:.2f} {change_symbol}{abs(change):.2f}({change_percent:.2f}%) {source_color}[{source_text}]\033[0m - {current_time} (#{iteration+1})", end="")
                
                # 5회마다 한 번씩 상세 로그 출력
                if iteration % 5 == 0:
                    print(f"\n💡 상세 정보: 데이터 소스={data_source}, 캐시 경과={cache_age:.1f}초")
                
                iteration += 1
                
                # 지정된 시간이 지나면 종료
                if duration and time.time() - start_time >= duration:
                    break
                
                # 대기 시간
                time.sleep(interval)
            else:
                print(f"\n❌ {symbol}에 대한 시세 정보를 가져오지 못했습니다.")
                time.sleep(interval)
        
        print(f"\n\n✅ 모니터링 종료 (총 {iteration}회 갱신)")
        print(f"📊 수집된 데이터 포인트: {len(prices)}개")
    
    except KeyboardInterrupt:
        print(f"\n\n⏹️ 사용자에 의해 모니터링이 중단되었습니다. (총 {iteration}회 갱신)")
    finally:
        # 메모리 정리
        plt.close('all')
    



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='주식 시세 REST API 테스트 도구')
    parser.add_argument('symbol', type=str, help='조회할 주식 심볼(예: AAPL, MSFT)')
    parser.add_argument('--monitor', '-m', action='store_true', help='실시간 모니터링 모드 활성화')
    parser.add_argument('--interval', '-i', type=int, default=5, help='갱신 간격(초)')
    parser.add_argument('--duration', '-d', type=int, help='모니터링 지속 시간(초)')
    parser.add_argument('--host', type=str, default='localhost', help='API 서버 호스트')
    parser.add_argument('--port', type=str, default='8000', help='API 서버 포트')
    
    args = parser.parse_args()
    
    if args.monitor:
        # 설치되지 않은 경우 필요한 패키지 설치 안내
        try:
            import matplotlib
            import pandas
        except ImportError:
            print("이 기능을 사용하려면 matplotlib과 pandas가 필요합니다.")
            print("다음 명령어로 설치하세요: pip install matplotlib pandas")
            sys.exit(1)
            
        print(f"{args.symbol} 주식 시세 모니터링 시작 (간격: {args.interval}초)")
        create_real_time_plot(args.symbol, args.interval, args.duration, args.host, args.port)
    else:
        # 단일 조회 모드
        quote = get_stock_quote(args.symbol, args.host, args.port)
        print_quote_info(quote)
