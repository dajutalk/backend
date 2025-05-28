from asyncio import Lock
from fastapi import WebSocket
import json
import logging
from stock.backend.services.finnhub_service import get_stock_data_for_broadcast

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

clients=[]
clients_lock =Lock()

async def safe_add_client(ws: WebSocket, symbol: str):
    async with clients_lock:
        clients.append({"websocket": ws, "symbol": symbol})
        logger.info(f"클라이언트 추가됨: {symbol}, 현재 접속자 수: {len(clients)}")

async def safe_remove_client(ws: WebSocket):
    async with clients_lock:
        clients[:] = [
            client for client in clients if client["websocket"] != ws
        ]
        logger.info(f"클라이언트 제거됨, 현재 접속자 수: {len(clients)}")

async def broadcast_stock_data(data: dict):
    """웹소켓 클라이언트에게 주식 데이터를 브로드캐스트"""
    try:
        symbol = data["data"][0]["s"]
        logger.info(f"브로드캐스트: {symbol}")
        
        async with clients_lock:
            for client in clients:
                if client["symbol"] == symbol:
                    try:
                        await client["websocket"].send_text(json.dumps(data))
                    except Exception as e:
                        logger.error(f"전송 실패: {e}")
    except Exception as e:
        logger.error(f"브로드캐스트 중 오류: {e}")

async def send_rest_api_data(symbol: str):
    """REST API로 가져온 데이터를 해당 심볼 구독자들에게 전송"""
    from stock.backend.services.finnhub_service import get_stock_data_for_broadcast
    
    # 가상화폐가 아닌 경우에만 처리
    if not symbol.startswith("BINANCE:"):
        data = get_stock_data_for_broadcast(symbol)
        if data:
            await broadcast_stock_data(data)