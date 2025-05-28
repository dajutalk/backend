from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from stock.backend.utils.ws_manager import safe_add_client, safe_remove_client
import threading
import asyncio
import json
from stock.backend.services.stock_service import run_ws
from stock.backend.services.finnhub_service import get_stock_quote
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

@rest_router.get("/symbols")
async def get_available_symbols():
    """
    API를 통해 조회 가능한 샘플 주식 심볼 목록 반환
    """
    return {
        "stocks": [
            {"symbol": "AAPL", "name": "Apple Inc."},
            {"symbol": "MSFT", "name": "Microsoft Corporation"},
            {"symbol": "GOOGL", "name": "Alphabet Inc."},
            {"symbol": "AMZN", "name": "Amazon.com, Inc."},
            {"symbol": "TSLA", "name": "Tesla, Inc."},
            {"symbol": "META", "name": "Meta Platforms, Inc."},
            {"symbol": "NVDA", "name": "NVIDIA Corporation"},
            {"symbol": "JPM", "name": "JPMorgan Chase & Co."},
        ],
        "crypto": [
            {"symbol": "BINANCE:BTCUSDT", "name": "Bitcoin"},
            {"symbol": "BINANCE:ETHUSDT", "name": "Ethereum"},
            {"symbol": "BINANCE:BNBUSDT", "name": "Binance Coin"},
            {"symbol": "BINANCE:SOLUSDT", "name": "Solana"},
        ]
    }




