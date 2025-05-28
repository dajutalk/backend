import websocket
import json
import time
import sys

def on_message(ws, message):
    """웹소켓 메시지 수신 시 호출되는 함수"""
    print(f"수신 메시지: {message}")
    try:
        data = json.loads(message)
        if 'data' in data and len(data['data']) > 0:
            for item in data['data']:
                print(f"심볼: {item.get('s')}, 가격: {item.get('p')}, 거래량: {item.get('v')}")
    except json.JSONDecodeError:
        print(f"JSON 파싱 실패: {message}")
    except Exception as e:
        print(f"처리 중 오류: {e}")

def on_error(ws, error):
    """에러 발생 시 호출되는 함수"""
    print(f"에러 발생: {error}")

def on_close(ws, close_status_code, close_msg):
    """연결 종료 시 호출되는 함수"""
    print(f"연결 종료: {close_status_code} - {close_msg}")

def on_open(ws):
    """연결 수립 시 호출되는 함수"""
    print("연결 성공!")

if __name__ == "__main__":
    # 명령줄 인자로 심볼을 받거나 기본값 사용
    symbol = sys.argv[1] if len(sys.argv) > 1 else "BINANCE:BTCUSDT"
    
    # WebSocket URL 설정 (심볼 포함)
    url = f"ws://localhost:8000/ws/stocks?symbol={symbol}"
    print(f"연결 중: {url}")
    
    # 웹소켓 연결 설정
    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # 웹소켓 연결 유지
    ws.run_forever()
