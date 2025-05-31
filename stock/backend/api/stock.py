from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from stock.backend.utils.ws_manager import safe_add_client, safe_remove_client
import threading
import asyncio
import json
from stock.backend.services.stock_service import run_ws
from stock.backend.services.finnhub_service import get_stock_quote, get_stock_symbols, get_crypto_symbols
from typing import List, Optional
import time

router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
    responses={404: {"description": "Not found"}},
)

# REST API 라우트를 위한 새 라우터
rest_router = APIRouter(
    prefix="/api/stocks",
    tags=["Stocks"],
    responses={404: {"description": "Not found"}},
)

running_threads = {}

@router.websocket("/stocks")
async def websocket_endpoint(websocket: WebSocket, symbol= Query(...)):
    await websocket.accept()
    await safe_add_client(websocket, symbol)

    if symbol not in running_threads:
        loop = asyncio.get_event_loop()
        thread = threading.Thread(target=run_ws, args=(loop, symbol), daemon=True)
        thread.start()
        running_threads[symbol] = thread

    try:
        while True:
            await asyncio.sleep(10)
            await websocket.send_text(json.dumps({'type':'ping'}))
    except WebSocketDisconnect:
        await safe_remove_client(websocket)

# REST API 엔드포인트 - 주식 시세 정보 수정
@rest_router.get("/quote")
async def get_stock_quote_endpoint(symbol: str = Query(...)):
    """
    특정 주식 심볼의 실시간 시세 정보를 반환하는 REST API 엔드포인트
    이 엔드포인트는 서버 측에서 주기적으로 업데이트된 데이터를 반환합니다.
    
    :param symbol: 주식 심볼 (예: AAPL, MSFT)
    :return: 주식 시세 정보 {c: 현재가, d: 변동폭, dp: 변동률(%), h: 고가, l: 저가, o: 시가, pc: 전일 종가}
    """
    if symbol.startswith("BINANCE:"):
        raise HTTPException(
            status_code=400, 
            detail="가상화폐는 /ws/stocks 웹소켓 엔드포인트를 통해 조회하세요"
        )
    
    # stock_service에서 캐시된 데이터 조회
    from stock.backend.services.stock_service import get_cached_stock_data, register_symbol
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info(f"📡 REST API 요청 수신: {symbol}")
    
    # 캐시된 데이터 조회
    data = get_cached_stock_data(symbol)
    
    if data:
        # 데이터 소스 정보 추출
        data_source = data.get('_data_source', 'unknown')
        cache_age = data.get('_cache_age', 0)
        
        # 캐시 경과시간으로 추가 판단 (더 정확한 판단)
        if data_source == 'cache' and cache_age < 60:
            final_source = 'cache'
        elif data_source == 'api' or cache_age < 5:  # 5초 이내면 최근 API 호출
            final_source = 'api'
        else:
            final_source = 'cache'
        
        logger.info(f"💾 응답 데이터 소스: {final_source}, 캐시 경과시간: {cache_age:.1f}초")
        
        response_data = {
            "c": data.get('c', 0),       # 현재 가격
            "d": data.get('d', 0),       # 변동폭 
            "dp": data.get('dp', 0),     # 변동률(%)
            "h": data.get('h', 0),       # 고가
            "l": data.get('l', 0),       # 저가
            "o": data.get('o', 0),       # 시가
            "pc": data.get('pc', 0),     # 전일 종가
            "t": int(time.time() * 1000), # 현재 타임스탬프
            "update_time": data.get('update_time', int(time.time())), # 마지막 업데이트 시간
            "data_source": final_source,  # 데이터 소스 (cache/api)
            "cache_age": cache_age       # 캐시 경과 시간 (초)
        }
        
        # 응답 로그
        if final_source == 'cache':
            logger.info(f"📋 캐시 데이터 응답: {symbol} (경과: {cache_age:.1f}초)")
        else:
            logger.info(f"🌐 API 데이터 응답: {symbol} (신규)")
            
        return response_data
    else:
        logger.error(f"❌ 데이터 없음: {symbol}")
        raise HTTPException(status_code=404, detail=f"심볼 '{symbol}'의 데이터를 찾을 수 없습니다")

# 주식 목록 가져오기 - 미국(US) 거래소만 지원하며 상위 30개만 반환
@rest_router.get("/exchange")
async def get_exchange_stocks():
    """
    미국(US) 거래소에서 거래되는 주식 목록 상위 30개를 반환하는 API
    
    :return: 미국 주식 심볼 목록 상위 60개
    """
    # 미국 주식으로 고정
    exchange = "US"
    result = await get_stock_symbols(exchange, currency="USD")
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # 상위 60개만 반환하고 symbol 값만 추출
    limited_result = result[:60] if len(result) > 60 else result
    return [item.get("symbol") for item in limited_result if item.get("symbol")]

# 암호화폐 심볼 목록 가져오기 - 바이낸스만 지원
@rest_router.get("/crypto/symbols")
async def get_crypto_symbols_endpoint():
    """
    바이낸스 거래소의 암호화폐 심볼 목록을 반환하는 API
    
    :return: 바이낸스 암호화폐 심볼 목록
    """
    # 바이낸스로 고정
    exchange = "binance"
    result = await get_crypto_symbols(exchange)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # 상위 30개만 반환
    return result[:30] if len(result) > 30 else result




