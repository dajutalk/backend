import asyncio
import websocket
import json
import threading
import time
import requests
from stock.backend.utils.ws_manager import broadcast_stock_data
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

API_KEY = os.getenv("FINNHUB_API_KEY")
loop = asyncio.get_event_loop()

# 주식 데이터 캐시
stock_cache = {}
last_update_time = {}
cache_lock = threading.Lock()

def run_ws(loop, symbol):
    def on_message(ws, message):
        try:
            data = json.loads(message)
            asyncio.run_coroutine_threadsafe(broadcast_stock_data(data), loop)
        except Exception as e:
            print("수신 처리 중 에러:", e)

    def on_open(ws):
        ws.send(json.dumps({
            "type": "subscribe",
            "symbol": symbol
        }))
        print(f" {symbol} 구독 시작")

    ws = websocket.WebSocketApp(
        f"wss://ws.finnhub.io?token={API_KEY}",
        on_message=on_message,
        on_open=on_open
    )
    ws.run_forever()

# 모든 활성 심볼에 대한 업데이트를 관리
active_symbols = set()
update_thread = None
thread_running = False

def update_stock_data(symbol):
    """주식 데이터를 업데이트하고 캐시에 저장"""
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
        logger.info(f"주식 업데이트 요청: {symbol}")
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'c' in data:
                with cache_lock:
                    stock_cache[symbol] = data
                    last_update_time[symbol] = time.time()
                logger.info(f"주식 데이터 업데이트 완료: {symbol}")
                return True
            else:
                logger.error(f"유효하지 않은 응답: {data}")
        else:
            logger.error(f"API 요청 실패: {response.status_code}")
            
        return False
    except Exception as e:
        logger.error(f"업데이트 중 오류: {e}")
        return False

def periodic_update_worker():
    """모든 활성 심볼에 대해 주기적으로 업데이트하는 워커 스레드"""
    global thread_running
    
    while thread_running:
        try:
            # 활성 심볼 목록 복사
            with cache_lock:
                symbols = list(active_symbols)
            
            current_time = time.time()
            symbols_to_update = []
            
            # 업데이트가 필요한 심볼 확인
            for symbol in symbols:
                if symbol not in last_update_time or (current_time - last_update_time.get(symbol, 0)) >= 60:
                    symbols_to_update.append(symbol)
            
            # 업데이트 실행
            for symbol in symbols_to_update:
                update_stock_data(symbol)
                # API 요청 제한을 위해 요청 간 간격 두기
                time.sleep(1.2)  # 초당 1회 미만 (분당 50회 이하로 유지)
            
            # 다음 검사 주기까지 대기
            time.sleep(5)
            
        except Exception as e:
            logger.error(f"주기적 업데이트 중 오류: {e}")
            time.sleep(10)

def register_symbol(symbol):
    """심볼을 활성 목록에 등록하고 필요하면 업데이트 스레드 시작"""
    global update_thread, thread_running
    
    with cache_lock:
        active_symbols.add(symbol)
        logger.info(f"심볼 등록: {symbol}, 현재 활성 심볼 수: {len(active_symbols)}")
        
        # 스레드가 실행 중이 아니면 시작
        if not thread_running:
            thread_running = True
            update_thread = threading.Thread(target=periodic_update_worker, daemon=True)
            update_thread.start()
            logger.info("주기적 업데이트 스레드 시작")
    
    # 즉시 초기 데이터 가져오기
    update_stock_data(symbol)

def get_cached_stock_data(symbol):
    """캐시된 주식 데이터 조회, 없으면 업데이트 후 반환"""
    with cache_lock:
        # 캐시에 있는지 확인
        if symbol in stock_cache:
            return stock_cache[symbol]
    
    # 캐시에 없으면 등록하고 업데이트
    register_symbol(symbol)
    
    # 업데이트 후 다시 확인
    with cache_lock:
        if symbol in stock_cache:
            return stock_cache[symbol]
    
    return None

