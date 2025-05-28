import websocket
import json
import time
import sys
import threading
import random
import argparse
from datetime import datetime

# 연결 상태 플래그
is_connected = False
# 메시지 이력
message_history = []

def on_message(ws, message):
    """웹소켓 메시지 수신 시 호출되는 함수"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    try:
        # JSON 파싱 시도
        data = json.loads(message)
        sender = data.get("username", "Unknown")
        msg = data.get("message", "")
        
        # 콘솔 출력 및 메시지 이력 저장
        formatted_msg = f"[{timestamp}] {sender}: {msg}"
        print(f"\n{formatted_msg}")
        message_history.append(formatted_msg)
        
    except json.JSONDecodeError:
        # 단순 문자열 메시지인 경우
        formatted_msg = f"[{timestamp}] 메시지: {message}"
        print(f"\n{formatted_msg}")
        message_history.append(formatted_msg)
    
    except Exception as e:
        print(f"\n메시지 처리 오류: {e}")
    
    print("\n> ", end='', flush=True)

def on_error(ws, error):
    """에러 발생 시 호출되는 함수"""
    print(f"\n연결 오류: {error}")

def on_close(ws, close_status_code, close_msg):
    """연결 종료 시 호출되는 함수"""
    global is_connected
    is_connected = False
    print(f"\n연결 종료됨: {close_status_code} - {close_msg}")
    
    # 메시지 이력 저장
    if args.save_log and message_history:
        filename = f"chat_log_{args.symbol.replace(':', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"채팅 로그 - {args.symbol}\n")
            f.write(f"시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 50 + "\n\n")
            for msg in message_history:
                f.write(f"{msg}\n")
        print(f"채팅 로그가 {filename}에 저장되었습니다.")

def on_open(ws):
    """연결 수립 시 호출되는 함수"""
    global is_connected
    is_connected = True
    print(f"\n{args.symbol} 채팅방에 연결되었습니다.")
    print(f"사용자 이름: {args.username}")
    print("\n명령어:")
    print("  /exit - 채팅방 나가기")
    print("  /users - 현재 접속 중인 사용자 목록 (서버에서 지원하는 경우)")
    print("  /clear - 콘솔 화면 지우기")
    
    # 입장 메시지 전송
    ws.send(json.dumps({
        "type": "chat_message",
        "message": f"{args.greeting if args.greeting else '안녕하세요! 채팅방에 입장했습니다.'}",
        "username": args.username
    }))
    
    # 사용자 입력 스레드 시작
    threading.Thread(target=input_loop, args=(ws,), daemon=True).start()

def input_loop(ws):
    """사용자 입력을 처리하는 스레드 함수"""
    global is_connected
    
    print("\n> ", end='', flush=True)
    
    while is_connected:
        try:
            user_input = input()
            
            # 연결이 끊어진 경우
            if not is_connected:
                break
            
            # 명령어 처리
            if user_input.startswith('/'):
                command = user_input.lower().strip()
                
                if command == '/exit':
                    print("채팅방을 나갑니다...")
                    ws.send(json.dumps({
                        "type": "chat_message",
                        "message": "채팅방을 떠났습니다.",
                        "username": args.username
                    }))
                    ws.close()
                    break
                
                elif command == '/clear':
                    # 콘솔 화면 지우기
                    print('\033c', end='')
                    print(f"\n{args.symbol} 채팅방")
                    print("> ", end='', flush=True)
                    continue
                
                elif command == '/users':
                    # 사용자 목록 요청 (서버에서 지원하는 경우)
                    ws.send(json.dumps({"type": "users_request"}))
                    continue
                
                else:
                    print(f"알 수 없는 명령어: {command}")
                    print("> ", end='', flush=True)
                    continue
            
            # 일반 메시지 전송
            ws.send(json.dumps({
                "type": "chat_message",
                "message": user_input,
                "username": args.username
            }))
            
        except Exception as e:
            if is_connected:
                print(f"\n오류 발생: {e}")
                print("> ", end='', flush=True)

if __name__ == "__main__":
    # 인자 파서 설정
    parser = argparse.ArgumentParser(description='실시간 채팅 테스트 도구')
    
    parser.add_argument('--symbol', type=str, default='BINANCE:BTCUSDT',
                        help='채팅방 심볼 (예: BINANCE:BTCUSDT)')
    parser.add_argument('--username', type=str, default=f"User_{random.randint(1000, 9999)}",
                        help='채팅에서 사용할 이름')
    parser.add_argument('--host', type=str, default='localhost',
                        help='웹소켓 서버 주소')
    parser.add_argument('--port', type=int, default=8000,
                        help='웹소켓 서버 포트')
    parser.add_argument('--greeting', type=str,
                        help='입장 시 자동 전송할 메시지')
    parser.add_argument('--save-log', action='store_true',
                        help='채팅 종료 시 로그 파일 저장')
    
    args = parser.parse_args()
    
    # 웹소켓 연결 URL 생성
    ws_url = f"ws://{args.host}:{args.port}/ws/chat?symbol={args.symbol}"
    print(f"연결 중: {ws_url}")
    
    # 웹소켓 클라이언트 생성 및 실행
    websocket.enableTrace(False)
    ws = websocket.WebSocketApp(
        ws_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    try:
        ws.run_forever()
    except KeyboardInterrupt:
        print("\n프로그램이 강제 종료되었습니다.")
    finally:
        if is_connected:
            is_connected = False
