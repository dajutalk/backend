from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from stock.backend.utils.ws_manager import safe_add_client, safe_remove_client
import threading
import asyncio
import json
from stock.backend.services.stock_service import run_ws
from stock.backend.services.finnhub_service import get_stock_quote, get_stock_symbols, get_crypto_symbols
from typing import List, Optional

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

# REST API 엔드포인트 - 주식 시세 정보 수정 및 디버깅
@rest_router.get("/quote")
async def get_stock_quote_endpoint(symbol: str = Query(...)):
    """
    특정 주식 심볼의 실시간 시세 정보를 반환하는 REST API 엔드포인트
    
    :param symbol: 주식 심볼 (예: AAPL, MSFT)
    :return: 주식 시세 정보 {c: 현재가, d: 변동폭, dp: 변동률(%), h: 고가, l: 저가, o: 시가, pc: 전일 종가}
    """
    if symbol.startswith("BINANCE:"):
        raise HTTPException(
            status_code=400, 
            detail="가상화폐는 /ws/stocks 웹소켓 엔드포인트를 통해 조회하세요"
        )
    
    # 디버깅 로그 추가
    print(f"Quote 요청: 심볼={symbol}")
    
    # 직접 Finnhub API 호출
    import requests
    import os
    
    API_KEY = os.getenv("FINNHUB_API_KEY")
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Finnhub API 키가 설정되지 않았습니다")
    
    try:
        url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={API_KEY}"
        print(f"API 요청: {url}")
        
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"API 응답 오류: {response.status_code}, {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"Finnhub API 오류: {response.text}")
        
        data = response.json()
        print(f"API 응답: {data}")
        
        # 응답 검증
        if 'c' not in data:
            print("유효하지 않은 응답 형식")
            raise HTTPException(status_code=500, detail="Finnhub API에서 유효하지 않은 응답 형식")
        
        # 응답 데이터 반환
        return {
            "c": data.get('c', 0),       # 현재 가격

        }
    except Exception as e:
        print(f"예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"API 요청 중 오류 발생: {str(e)}")

# 주식 목록 가져오기 - 미국(US) 거래소만 지원하며 상위 30개만 반환
@rest_router.get("/exchange")
async def get_exchange_stocks():
    """
    미국(US) 거래소에서 거래되는 주식 목록 상위 30개를 반환하는 API
    
    :return: 미국 주식 목록 상위 30개
    """
    # 미국 주식으로 고정
    exchange = "US"
    result = await get_stock_symbols(exchange, currency="USD")
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # 상위 30개만 반환
    return result[:30] if len(result) > 30 else result

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




