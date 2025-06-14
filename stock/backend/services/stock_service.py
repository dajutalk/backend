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
                current_time = time.time()
                # 캐시 정보 추가
                data['_cache_info'] = {
                    'cached_at': current_time,
                    'source': 'api'
                }
                data['_cache_age'] = 0
                
                with cache_lock:
                    stock_cache[symbol] = data
                    last_update_time[symbol] = current_time
                logger.info(f"주식 데이터 업데이트 완료: {symbol} (API 호출)")
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
    current_time = time.time()
    
    with cache_lock:
        # 캐시에 있는지 확인
        if symbol in stock_cache:
            cached_data = stock_cache[symbol].copy()
            # 캐시 경과 시간 계산
            cache_info = cached_data.get('_cache_info', {})
            cached_at = cache_info.get('cached_at', 0)
            cache_age = current_time - cached_at
            cached_data['_cache_age'] = cache_age
            cached_data['_data_source'] = 'cache'  # 명시적으로 캐시에서 가져옴을 표시
            logger.info(f" 캐시에서 데이터 반환: {symbol} (캐시 경과: {cache_age:.1f}초)")
            return cached_data
    
    # 캐시에 없으면 등록하고 업데이트
    logger.info(f" 캐시에 없음, 새로 API 호출: {symbol}")
    register_symbol(symbol)
    
    # 업데이트 후 다시 확인
    with cache_lock:
        if symbol in stock_cache:
            cached_data = stock_cache[symbol].copy()
            cached_data['_cache_age'] = 0  # 방금 업데이트됨
            cached_data['_data_source'] = 'api'  # API에서 새로 가져옴을 표시
            logger.info(f" 새로 업데이트된 데이터 반환: {symbol}")
            return cached_data
    
    return None

def cleanup_inactive_symbols():
    """비활성화된 심볼들을 캐시에서 정리"""
    global active_symbols
    
    current_time = time.time()
    symbols_to_remove = []
    
    with cache_lock:
        for symbol in list(stock_cache.keys()):
            # 12시간 이상 업데이트되지 않은 심볼 제거
            if symbol not in active_symbols and current_time - last_update_time.get(symbol, 0) > 43200:
                symbols_to_remove.append(symbol)
        
        for symbol in symbols_to_remove:
            stock_cache.pop(symbol, None)
            last_update_time.pop(symbol, None)
            logger.info(f"비활성 심볼 캐시 정리: {symbol}")

def stop_update_thread():
    """업데이트 스레드 중지"""
    global thread_running
    thread_running = False
    logger.info("주기적 업데이트 스레드 중지됨")

def get_cache_statistics():
    """캐시 통계 정보 반환"""
    with cache_lock:
        return {
            "cached_symbols": len(stock_cache),
            "active_symbols": len(active_symbols),
            "last_updates": {symbol: time.time() - last_time for symbol, last_time in last_update_time.items()}
        }

# 상위 10개 암호화폐 목록
TOP_10_CRYPTOS = [
    "BTC", "ETH", "USDT", "XRP", "BNB", 
    "SOL", "USDC", "DOGE", "ADA", "TRX"
]

# 암호화폐 데이터 캐시 (별도 관리)
crypto_cache = {}
crypto_last_update_time = {}
crypto_thread = None
crypto_thread_running = False

def update_crypto_data(symbol):
    """암호화폐 데이터를 업데이트하고 캐시에 저장"""
    try:
        # 바이낸스 심볼 형식으로 변환 (예: BTC -> BINANCE:BTCUSDT)
        binance_symbol = f"BINANCE:{symbol}USDT"
        url = f"https://finnhub.io/api/v1/quote?symbol={binance_symbol}&token={API_KEY}"
        logger.info(f"암호화폐 업데이트 요청: {symbol} ({binance_symbol})")
        
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'c' in data and data['c'] != 0:  # 유효한 가격 데이터 확인
                current_time = time.time()
                
                # 암호화폐 데이터를 웹소켓 형식으로 변환
                crypto_data = {
                    's': binance_symbol,  # 심볼 (BINANCE:BTCUSDT 형식)
                    'p': str(data['c']),  # 현재 가격 (문자열로 변환)
                    'v': str(data.get('v', 0)),  # 거래량 (문자열로 변환)
                    't': int(time.time() * 1000),  # 타임스탬프 (밀리초)
                    

                    
                    # 캐시 메타데이터
                    '_cache_info': {
                        'cached_at': current_time,
                        'source': 'api'
                    },
                    '_cache_age': 0,
                    '_data_source': 'api'
                }
                
                with cache_lock:
                    crypto_cache[symbol] = crypto_data
                    crypto_last_update_time[symbol] = current_time
                
                logger.info(f"암호화폐 데이터 업데이트 완료: {symbol} = ${data['c']:.4f}")
                return True
            else:
                logger.error(f"유효하지 않은 암호화폐 응답: {symbol} - {data}")
        else:
            logger.error(f"암호화폐 API 요청 실패: {symbol} - {response.status_code}")
            
        return False
    except Exception as e:
        logger.error(f"암호화폐 업데이트 중 오류: {symbol} - {e}")
        return False

def crypto_periodic_update_worker():
    """암호화폐 데이터를 1분마다 업데이트하는 워커 스레드"""
    global crypto_thread_running
    
    logger.info(f" 암호화폐 자동 수집 시작 - {len(TOP_10_CRYPTOS)}개 코인")
    
    while crypto_thread_running:
        try:
            start_time = time.time()
            success_count = 0
            
            logger.info(f" 암호화폐 데이터 수집 시작 - {len(TOP_10_CRYPTOS)}개 처리")
            
            # 모든 암호화폐 업데이트
            for symbol in TOP_10_CRYPTOS:
                if not crypto_thread_running:
                    break
                    
                if update_crypto_data(symbol):
                    success_count += 1
                    
                    #  암호화폐 데이터 DB 저장 프로세스 설명:
                    # 1. API에서 받은 데이터를 캐시에 저장 후
                    # 2. 캐시에서 데이터를 가져와서 DB 저장용 형식으로 변환
                    # 3. crypto_service를 통해 crypto_quotes 테이블에 저장
                    
                    # DB 저장 (crypto_service 사용)
                    try:
                        from stock.backend.services.crypto_service import crypto_service
                        crypto_data_obj = crypto_cache.get(symbol)
                        
                        logger.info(f" 캐시에서 가져온 데이터: {symbol} -> {crypto_data_obj}")
                        
                        if crypto_data_obj:
                            # CryptoQuote 형식으로 변환하여 저장
                            crypto_quote_data = {
                                "symbol": symbol,  # BTC, ETH 등
                                "s": crypto_data_obj.get('s', ''),     # BINANCE:BTCUSDT
                                "p": crypto_data_obj.get('p', '0'),    # 현재가 (문자열)
                                "v": crypto_data_obj.get('v', '0'),    # 거래량 (문자열)
                                "t": crypto_data_obj.get('t', 0)       # 타임스탬프 (밀리초)
                            }
                            
                            #  타임스탬프 값 검증 및 로깅
                            timestamp_value = crypto_quote_data.get('t', 0)
                            logger.info(f" {symbol} 타임스탬프 값: {timestamp_value} ({type(timestamp_value)})")
                            
                            # 타임스탬프 범위 검증 (밀리초 단위)
                            if timestamp_value <= 0:
                                logger.error(f" {symbol} 잘못된 타임스탬프: {timestamp_value}")
                                continue
                            
                            # BIGINT 범위 검증 (2^63-1 = 9223372036854775807)
                            if timestamp_value > 9223372036854775807:
                                logger.error(f" {symbol} 타임스탬프 범위 초과: {timestamp_value}")
                                continue
                            
                            logger.info(f" DB 저장용 데이터 변환: {symbol} -> {crypto_quote_data}")
                            
                            if crypto_service.save_crypto_quote(crypto_quote_data):
                                logger.debug(f" {symbol} 암호화폐 데이터 DB 저장 완료")
                            else:
                                logger.error(f" {symbol} 암호화폐 데이터 DB 저장 실패")
                                #  실패 원인 분석을 위한 추가 로깅
                                logger.error(f" 실패한 데이터: {crypto_quote_data}")
                                logger.error(f" 캐시 원본 데이터: {crypto_data_obj}")
                        else:
                            logger.error(f" {symbol} 캐시에서 데이터를 찾을 수 없음")
                            
                    except Exception as e:
                        logger.error(f" {symbol} DB 저장 중 오류: {e}")
                        # 스택 트레이스 출력
                        import traceback
                        logger.error(f" 스택 트레이스:\n{traceback.format_exc()}")
                
                # API 요청 제한을 위한 지연
                time.sleep(1.2)
            
            elapsed_time = time.time() - start_time
            logger.info(f" 암호화폐 수집 완료: {success_count}/{len(TOP_10_CRYPTOS)} 성공 (소요: {elapsed_time:.1f}초)")
            
            # 다음 실행까지 대기 (1분 - 처리 시간)
            remaining_time = 60 - elapsed_time
            if remaining_time > 0:
                logger.info(f" 다음 암호화폐 수집까지 {remaining_time:.1f}초 대기...")
                time.sleep(remaining_time)
            else:
                logger.warning(f" 암호화폐 처리 시간이 1분 초과: {elapsed_time:.1f}초")
            
        except Exception as e:
            logger.error(f" 암호화폐 수집 루프 오류: {e}")
            time.sleep(10)
    
    logger.info(" 암호화폐 자동 수집 스레드 종료")

def start_crypto_collection():
    """암호화폐 자동 수집 시작"""
    global crypto_thread, crypto_thread_running
    
    if crypto_thread_running:
        logger.warning("암호화폐 수집이 이미 실행 중입니다")
        return
    
    # 초기 데이터 수집
    logger.info(" 암호화폐 초기 데이터 수집 시작")
    for symbol in TOP_10_CRYPTOS:
        if update_crypto_data(symbol):
            logger.info(f" {symbol} 초기 데이터 수집 완료")
        else:
            logger.error(f" {symbol} 초기 데이터 수집 실패")
        time.sleep(1.2)
    
    crypto_thread_running = True
    crypto_thread = threading.Thread(target=crypto_periodic_update_worker, daemon=True)
    crypto_thread.start()
    logger.info(" 암호화폐 자동 수집 스레드 시작")

def stop_crypto_collection():
    """암호화폐 자동 수집 중지"""
    global crypto_thread_running
    crypto_thread_running = False
    logger.info(" 암호화폐 자동 수집 중지됨")

def get_cached_crypto_data(symbol):
    """캐시된 암호화폐 데이터 조회"""
    current_time = time.time()
    
    with cache_lock:
        if symbol in crypto_cache:
            cached_data = crypto_cache[symbol].copy()
            cache_info = cached_data.get('_cache_info', {})
            cached_at = cache_info.get('cached_at', 0)
            cache_age = current_time - cached_at
            cached_data['_cache_age'] = cache_age
            cached_data['_data_source'] = 'cache'
            
            logger.info(f" 암호화폐 캐시 데이터 반환: {symbol} (경과: {cache_age:.1f}초)")
            return cached_data
    
    # 캐시에 없으면 즉시 업데이트
    logger.info(f" 암호화폐 캐시 없음, 새로 API 호출: {symbol}")
    if update_crypto_data(symbol):
        with cache_lock:
            if symbol in crypto_cache:
                cached_data = crypto_cache[symbol].copy()
                cached_data['_cache_age'] = 0
                cached_data['_data_source'] = 'api'
                logger.info(f" 새 암호화폐 데이터 반환: {symbol}")
                return cached_data
    
    return None

def get_crypto_statistics():
    """암호화폐 캐시 통계 정보 반환"""
    with cache_lock:
        return {
            "cached_cryptos": len(crypto_cache),
            "monitored_cryptos": len(TOP_10_CRYPTOS),
            "crypto_symbols": list(TOP_10_CRYPTOS),
            "thread_running": crypto_thread_running,
            "last_updates": {
                symbol: time.time() - last_time 
                for symbol, last_time in crypto_last_update_time.items()
            }
        }

