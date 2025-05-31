from asyncio import Lock
from fastapi import WebSocket
import json
import logging
from stock.backend.services.finnhub_service import get_stock_data_for_broadcast
from stock.backend.services.db_service import db_service

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
        
        # 📊 실시간 데이터를 데이터베이스에 저장
        for item in data["data"]:
            db_service.save_stock_price(item)
        
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

async def broadcast_to_symbol_subscribers(symbol: str, data: dict):
    """특정 심볼 구독자들에게만 데이터 브로드캐스트"""
    disconnected_clients = []
    
    async with clients_lock:
        for client in clients:
            if client["symbol"] == symbol:
                try:
                    await client["websocket"].send_text(json.dumps(data))
                except Exception as e:
                    logger.error(f"클라이언트 전송 실패: {e}")
                    disconnected_clients.append(client)
    
    # 연결이 끊어진 클라이언트 제거
    if disconnected_clients:
        async with clients_lock:
            for client in disconnected_clients:
                if client in clients:
                    clients.remove(client)
        logger.info(f"연결 끊어진 클라이언트 {len(disconnected_clients)}개 제거됨")

async def get_active_symbols():
    """현재 활성화된 심볼 목록 반환"""
    async with clients_lock:
        return list(set(client["symbol"] for client in clients))