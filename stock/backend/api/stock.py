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

# REST API 엔드포인트 추가
@rest_router.get("/quote/{symbol}")
async def get_stock_quote_endpoint(symbol: str):
    """
    특정 주식 심볼의 실시간 시세 정보를 반환하는 REST API 엔드포인트
    
    :param symbol: 주식 심볼 (예: AAPL, MSFT)
    :return: 주식 시세 정보
    """
    if symbol.startswith("BINANCE:"):
        raise HTTPException(
            status_code=400, 
            detail="가상화폐는 /ws/stocks 웹소켓 엔드포인트를 통해 조회하세요"
        )
    
    quote = get_stock_quote(symbol)
    if quote:
        return quote
    else:
        raise HTTPException(status_code=404, detail=f"심볼 '{symbol}'의 데이터를 찾을 수 없습니다")

# 거래소 주식 목록 가져오기 엔드포인트 수정 - 파라미터 간소화 및 상위 30개만 반환
@rest_router.get("/exchange/{exchange}")
async def get_exchange_stocks(exchange: str):
    """
    특정 거래소에서 거래되는 주식 목록 상위 30개를 반환하는 API
    
    :param exchange: 거래소 코드 (예: US)
    :return: 주식 목록 상위 30개
    """
    # 미국 주식만 지원하도록 currency는 USD로 고정
    result = await get_stock_symbols(exchange, currency="USD")
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    # 상위 30개만 반환
    return result[:30] if len(result) > 30 else result

# 암호화폐 심볼 목록 가져오기 엔드포인트 추가
@rest_router.get("/crypto/symbols/{exchange}")
async def get_crypto_symbols_endpoint(exchange: str):
    """
    특정 거래소의 암호화폐 심볼 목록을 반환하는 API
    
    :param exchange: 암호화폐 거래소 이름 (예: binance, coinbase)
    :return: 암호화폐 심볼 목록
    """
    result = await get_crypto_symbols(exchange)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result




