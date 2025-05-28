import websocket
import json
import time
import sys
import threading
import random
import argparse

# 연결 상태 플래그
is_connected = False
# 사용자 이름
username = f"테스터_{random.randint(1000, 9999)}"

def on_message(ws, message):
    """웹소켓 메시지 수신 시 호출되는 함수"""
    print(f"\n수신 메시지: {message}")
    try:
        # 메시지가 JSON인 경우 파싱
        data = json.loads(message)
        if isinstance(data, dict):
            sender = data.get("username", "익명")
            msg = data.get("message", "")
            print(f"[{sender}] {msg}")
        else:
            # 일반 텍스트 메시지인 경우
            print(f"[메시지] {message}")
    except json.JSONDecodeError:
        # JSON이 아닌 경우 그대로 출력
        print(f"[메시지] {message}")
    except Exception as e:
        print(f"처리 중 오류: {e}")
    
    print("\n메시지 입력 (종료하려면 'exit' 입력): ", end='', flush=True)

def on_error(ws, error):
    """에러 발생 시 호출되는 함수"""
    print(f"\n에러 발생: {error}")

def on_close(ws, close_status_code, close_msg):
    """연결 종료 시 호출되는 함수"""
    global is_connected
    is_connected = False
    print(f"\n연결 종료: {close_status_code} - {close_msg}")

def on_open(ws):
    """연결 수립 시 호출되는 함수"""
    global is_connected
    is_connected = True
    print("\n채팅 서버에 연결되었습니다!")
    print(f"심볼: {args.symbol}")
    print(f"사용자 이름: {username}")
    print("\n대화에 참여하세요. 메시지를 입력하고 Enter를 누르세요.")
    print("채팅을 종료하려면 'exit'를 입력하세요.")
    
    # 입장 메시지 JSON 형식으로 전송
    entry_message = json.dumps({
        "type": "chat_message",
        "message": "채팅방에 입장했습니다.",
        "username": username
    })
    ws.send(entry_message)
    
    # 메시지 입력을 별도 스레드에서 처리
    threading.Thread(target=input_message_thread, args=(ws,)).start()

def input_message_thread(ws):
    """사용자 입력을 처리하는 스레드 함수"""
    global is_connected
    
    while is_connected:
        try:
            message = input("\n메시지 입력 (종료하려면 'exit' 입력): ")
            
            if not is_connected:
                break
                
            if message.lower() == 'exit':
                print("채팅을 종료합니다...")
                ws.close()
                break
                
            # 메시지 JSON 형식으로 전송
            ws.send(json.dumps({
                "type": "chat_message",
                "message": message,
                "username": username
            }))
        except Exception as e:
            print(f"메시지 전송 중 오류: {e}")
            if not is_connected:
                break

if __name__ == "__main__":
    # 명령행 인자 처리
    parser = argparse.ArgumentParser(description='심볼별 채팅 테스트 클라이언트')
    parser.add_argument('--symbol', type=str, default='BINANCE:BTCUSDT', 
                        help='채팅할 심볼 (예: BINANCE:BTCUSDT, NASDAQ:AAPL)')
    parser.add_argument('--username', type=str, help='사용자 이름 (기본값: 랜덤 생성)')
    parser.add_argument('--host', type=str, default='localhost', help='서버 호스트')
    parser.add_argument('--port', type=str, default='8000', help='서버 포트')
    
    args = parser.parse_args()
    
    # 사용자 이름 설정
    if args.username:
        username = args.username
    
    # WebSocket URL 설정 (심볼 포함)
    url = f"ws://{args.host}:{args.port}/ws/chat?symbol={args.symbol}"
    print(f"연결 중: {url}")
    
    # 웹소켓 연결 설정
    websocket.enableTrace(False)  # 디버깅을 위한 자세한 로그를 원한다면 True로 설정
    ws = websocket.WebSocketApp(
        url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    # 웹소켓 연결 유지
    ws.run_forever()
    
    print("프로그램이 종료되었습니다.")
