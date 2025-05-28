import os
import time
import requests
import json
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()
API_KEY = os.getenv("FINNHUB_API_KEY")

# 캐시 데이터와 마지막 요청 시간을 저장할 변수
stock_cache: Dict[str, Dict[str, Any]] = {}
last_request_time: Dict[str, float] = {}
request_lock = threading.Lock()

def get_stock_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Finnhub API를 통해 주식 시세 정보를 가져오는 함수
    요청 제한을 고려하여 캐싱 로직 구현
    
    :param symbol: 주식 심볼 (예: AAPL, MSFT)
    :return: 주식 데이터 사전 또는 오류 시 None
    """
    current_time = time.time()
    
    # 가상화폐는 웹소켓으로 처리하므로 REST API 사용하지 않음
    if symbol.startswith("BINANCE:"):
        return None
    
    # 사용 가능한 캐시가 있는지 확인
    with request_lock:
        # 기존 캐시 확인
        if symbol in stock_cache:
            cache_age = current_time - last_request_time.get(symbol, 0)
            # 60초(1분) 이내의 데이터는 캐시 사용
            if cache_age < 60:
                logger.info(f"캐시된 데이터 반환: {symbol}, 경과 시간: {cache_age:.1f}초")
                return stock_cache[symbol]
        
        # 이 심볼에 대해 마지막 요청 후 최소 60초 지났는지 확인
        if symbol in last_request_time and current_time - last_request_time[symbol] < 60:
            logger.info(f"요청 제한으로 캐시된 데이터 반환: {symbol}")
            return stock_cache.get(symbol)
        
        # API 요청
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
            logger.info(f"Finnhub API 요청: {symbol}")
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                
                # 응답이 유효하면 캐시 업데이트
                if 'c' in data:  # 'c'는 현재 가격
                    formatted_data = {
                        's': symbol,                 # 심볼
                        'p': str(data['c']),         # 현재 가격
                        'v': str(data['v']),         # 거래량
                        'o': str(data['o']),         # 시가
                        'h': str(data['h']),         # 고가
                        'l': str(data['l']),         # 저가
                        'pc': str(data['pc']),       # 이전 종가
                        't': int(time.time() * 1000) # 타임스탬프 (밀리초)
                    }
                    
                    stock_cache[symbol] = formatted_data
                    last_request_time[symbol] = current_time
                    
                    return formatted_data
                else:
                    logger.error(f"유효하지 않은 응답: {data}")
            else:
                logger.error(f"API 요청 실패: {response.status_code}, {response.text}")
        
        except Exception as e:
            logger.error(f"API 요청 중 오류 발생: {e}")
        
        # 오류 시 기존 캐시가 있으면 반환
        return stock_cache.get(symbol)

def get_stock_data_for_broadcast(symbol: str) -> Optional[Dict[str, Any]]:
    """
    브로드캐스트용 주식 데이터 형식으로 반환하는 함수
    
    :param symbol: 주식 심볼
    :return: 웹소켓 브로드캐스트용 데이터 형식
    """
    quote = get_stock_quote(symbol)
    if quote:
        # 웹소켓 브로드캐스트용 형식으로 변환
        return {
            "type": "stock_update",
            "data": [quote]
        }
    return None

def update_stock_cache_periodically():
    """
    캐시된 모든 주식 심볼에 대해 주기적으로 업데이트하는 백그라운드 스레드 함수
    """
    while True:
        try:
            symbols_to_update = []
            
            # 업데이트가 필요한 심볼 목록 확인
            with request_lock:
                current_time = time.time()
                for symbol in list(stock_cache.keys()):
                    # 가상화폐는 제외
                    if symbol.startswith("BINANCE:"):
                        continue
                    
                    # 마지막 업데이트 후 60초 이상 지난 경우
                    if current_time - last_request_time.get(symbol, 0) >= 60:
                        symbols_to_update.append(symbol)
            
            # 업데이트가 필요한 각 심볼에 대해 API 요청
            for symbol in symbols_to_update:
                stock_data = get_stock_quote(symbol)
                if stock_data:
                    logger.info(f"백그라운드 업데이트 완료: {symbol}")
                
                # API 요청 제한 준수를 위해 요청 간 지연
                time.sleep(1.2)  # 1.2초 간격으로 최대 50개/분 유지
            
            # 다음 검사 주기까지 대기
            time.sleep(10)  # 10초마다 업데이트 필요한지 검사
            
        except Exception as e:
            logger.error(f"주기적 업데이트 중 오류: {e}")
            time.sleep(30)  # 오류 발생 시 30초 대기 후 재시도

# 모듈 초기화 시 백그라운드 스레드 시작
background_thread = threading.Thread(
    target=update_stock_cache_periodically, 
    daemon=True
)
background_thread.start()
