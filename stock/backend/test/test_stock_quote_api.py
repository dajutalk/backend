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
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"API 요청 실패: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"요청 중 오류 발생: {e}")
        return None

def print_quote_info(quote):
    """주식 시세 정보를 표준 출력으로 출력"""
    if not quote:
        print("데이터 없음")
        return
    
    # 가격 정보 출력
    print(f"\n{'=' * 50}")
    print(f"{quote.get('t', 0)}")
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
    
    print(f"{'=' * 50}\n")

def create_real_time_plot(symbol, interval=5, duration=None, host="localhost", port="8000"):
    """지정된 간격으로 주식 시세를 가져와 실시간 그래프로 표시"""
    plt.figure(figsize=(12, 6))
    plt.title(f"{symbol} Real-time Stock Price")
    plt.xlabel("Time")
    plt.ylabel("Price ($)")
    plt.grid(True)
    
    # 데이터 저장용
    times = []
    prices = []
    
    try:
        start_time = time.time()
        iteration = 0
        
        while True:
            # 주식 시세 데이터 요청
            quote = get_stock_quote(symbol, host, port)
            
            if quote:
                current_time = datetime.now().strftime('%H:%M:%S')
                price = quote.get('c', 0)
                
                # 데이터 추가
                times.append(current_time)
                prices.append(price)
                
                # 변동 정보
                change = quote.get('d', 0)
                change_percent = quote.get('dp', 0)
                change_symbol = "▲" if change >= 0 else "▼"
                
                # 콘솔에 현재 정보 출력
                print(f"\r현재 {symbol} 가격: ${price:.2f} {change_symbol} {abs(change):.2f} ({change_percent:.2f}%) - {current_time} (갱신: {iteration+1}회)", end="")
                
                # 그래프 업데이트
                plt.clf()
                plt.title(f"{symbol} Real-time Stock Price")
                plt.xlabel("Time")
                plt.ylabel("Price ($)")
                plt.grid(True)
                plt.plot(times, prices, 'b-')
                plt.plot(times[-1:], prices[-1:], 'ro')  # 최신 가격 빨간점으로 강조
                
                # 가격 레이블 표시
                for i in range(0, len(times), max(1, len(times)//5)):
                    plt.text(times[i], prices[i], f"${prices[i]:.2f}")
                
                plt.xticks(rotation=45)
                plt.tight_layout()
                plt.pause(0.1)
                
                iteration += 1
                
                # 지정된 시간이 지나면 종료
                if duration and time.time() - start_time >= duration:
                    break
                
                # 대기 시간
                time.sleep(interval)
            else:
                print(f"\n{symbol}에 대한 시세 정보를 가져오지 못했습니다.")
                time.sleep(interval)
        
        print("\n\n모니터링 종료")
    
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 모니터링이 중단되었습니다.")
    
    # 결과 데이터프레임 생성 및 저장
    df = pd.DataFrame({
        'time': times,
        'price': prices
    })
    
    filename = f"{symbol}_price_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    print(f"\n가격 데이터가 '{filename}'에 저장되었습니다.")
    
    # 최종 그래프 표시
    plt.figure(figsize=(12, 6))
    plt.title(f"{symbol} Stock Price Chart")
    plt.xlabel("Time")
    plt.ylabel("Price ($)")
    plt.grid(True)
    plt.plot(times, prices, 'b-', marker='o')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{symbol}_price_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
    plt.show()

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
