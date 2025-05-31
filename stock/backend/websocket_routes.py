import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from stock.backend.websocket_manager import manager
from stock.backend.data_service import DataService
from stock.backend.database import get_db  # 기존 데이터베이스 세션 가져오기
import logging
import json
import time

logger = logging.getLogger(__name__)

router = APIRouter()

# 백그라운드 태스크 상태 관리
background_task = None
is_broadcasting = False

@router.websocket("/ws/main")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    global background_task, is_broadcasting
    
    await manager.connect(websocket)
    
    # 첫 번째 클라이언트 연결 시 백그라운드 브로드캐스트 시작
    if not is_broadcasting and len(manager.active_connections) == 1:
        background_task = asyncio.create_task(broadcast_market_data(db))
        is_broadcasting = True
        logger.info("Started background broadcasting task")
    
    try:
        # 연결 즉시 실제 시장 데이터 전송
        from stock.backend.services.stock_service import get_cached_stock_data, get_cached_crypto_data, TOP_10_CRYPTOS
        
        # 주요 주식 데이터 수집
        stock_symbols = [
            "NVDA", "TSLA", "PLTR", "INTC", "AAPL", "BAC", "AMZN", "AMD", "GOOG", "MSFT",
            "META", "AVGO", "NFLX", "COST", "UNH", "MSTR", "LLY", "CRM", "V", "REGN",
            "APP", "WMT", "XOM", "MRVL", "ORCL", "JPM", "TXN", "ZS", "NOW", "MA",
            "IBM", "UBER", "JNJ", "AMAT", "HOOD", "ADI", "GE", "MU", "PANW",
            "INTU", "ABBV", "PG", "DELL", "CRWD", "SPOT", "LIN", "KO", "TMUS", "QCOM", "F"
        ]
        stocks_data = []
        
        for symbol in stock_symbols:
            stock_data = get_cached_stock_data(symbol)
            if stock_data:
                stocks_data.append({
                    "symbol": symbol,
                    "c": stock_data.get('c', 0),
                    "price": stock_data.get('c', 0),
                    "v": stock_data.get('v', 0),
                    "timestamp": stock_data.get('t', 0)
                })
        
        # 암호화폐 데이터 수집
        cryptos_data = []
        for symbol in TOP_10_CRYPTOS:
            crypto_data = get_cached_crypto_data(symbol)
            if crypto_data:
                cryptos_data.append({
                    "symbol": symbol,
                    "s": crypto_data.get('s', ''),
                    "p": float(crypto_data.get('p', 0)),
                    "price": float(crypto_data.get('p', 0)),
                    "v": crypto_data.get('v', 0),
                    "timestamp": crypto_data.get('t', 0)
                })
        
        # 초기 데이터 전송
        initial_data = {
            "type": "market_update",
            "data": {
                "stocks": stocks_data,
                "cryptos": cryptos_data
            },
            "timestamp": int(time.time() * 1000)
        }
        
        await manager.send_personal_message(initial_data, websocket)
        logger.info(f"Initial market data sent - {len(stocks_data)} stocks, {len(cryptos_data)} cryptos")
        
        # 클라이언트로부터 메시지 대기 (연결 유지)
        while True:
            try:
                message = await websocket.receive_text()
                logger.info(f"Received message from client: {message}")
                
                # 클라이언트 요청에 따른 즉시 데이터 전송
                if message == "get_latest":
                    # 최신 데이터 다시 수집
                    latest_stocks = []
                    for symbol in stock_symbols:
                        stock_data = get_cached_stock_data(symbol)
                        if stock_data:
                            latest_stocks.append({
                                "symbol": symbol,
                                "c": stock_data.get('c', 0),
                                "price": stock_data.get('c', 0),
                                "v": stock_data.get('v', 0),
                                "timestamp": stock_data.get('t', 0)
                            })
                    
                    latest_cryptos = []
                    for symbol in TOP_10_CRYPTOS:
                        crypto_data = get_cached_crypto_data(symbol)
                        if crypto_data:
                            latest_cryptos.append({
                                "symbol": symbol,
                                "s": crypto_data.get('s', ''),
                                "p": float(crypto_data.get('p', 0)),
                                "price": float(crypto_data.get('p', 0)),
                                "v": crypto_data.get('v', 0),
                                "timestamp": crypto_data.get('t', 0)
                            })
                    
                    latest_data = {
                        "type": "market_update",
                        "data": {
                            "stocks": latest_stocks,
                            "cryptos": latest_cryptos
                        },
                        "timestamp": int(time.time() * 1000)
                    }
                    
                    await manager.send_personal_message(latest_data, websocket)
                    logger.info(f"Latest data sent on request - {len(latest_stocks)} stocks, {len(latest_cryptos)} cryptos")
                    
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
        
        # 모든 클라이언트가 연결 해제되면 백그라운드 태스크 중지
        if len(manager.active_connections) == 0 and background_task:
            background_task.cancel()
            is_broadcasting = False
            logger.info("Stopped background broadcasting task")

async def broadcast_market_data(db: Session):
    """1분마다 시장 데이터를 모든 클라이언트에게 브로드캐스트"""
    while True:
        try:
            if manager.active_connections:
                # 주식 데이터 수집
                from stock.backend.services.stock_service import get_cached_stock_data, get_cached_crypto_data, TOP_10_CRYPTOS
                
                # 주요 주식 데이터 수집
                stock_symbols = [
                    "NVDA", "TSLA", "PLTR", "INTC", "AAPL", "BAC", "AMZN", "AMD", "GOOG", "MSFT",
                    "META", "AVGO", "NFLX", "COST", "UNH", "MSTR", "LLY", "CRM", "V", "REGN",
                    "APP", "WMT", "XOM", "MRVL", "ORCL", "JPM", "TXN", "ZS", "NOW", "MA",
                    "IBM", "UBER", "JNJ", "AMAT", "HOOD", "ADI", "GE", "MU", "PANW",
                    "INTU", "ABBV", "PG", "DELL", "CRWD", "SPOT", "LIN", "KO", "TMUS", "QCOM", "F"
                ]
                stocks_data = []
                
                for symbol in stock_symbols:
                    stock_data = get_cached_stock_data(symbol)
                    if stock_data:
                        stocks_data.append({
                            "symbol": symbol,
                            "c": stock_data.get('c', 0),  # 현재가
                            "price": stock_data.get('c', 0),  # 가격 (호환성)
                            "v": stock_data.get('v', 0),  # 거래량
                            "timestamp": stock_data.get('t', 0)
                        })
                
                # 암호화폐 데이터 수집
                cryptos_data = []
                for symbol in TOP_10_CRYPTOS:
                    crypto_data = get_cached_crypto_data(symbol)
                    if crypto_data:
                        cryptos_data.append({
                            "symbol": symbol,
                            "s": crypto_data.get('s', ''),
                            "p": float(crypto_data.get('p', 0)),  # 현재가
                            "price": float(crypto_data.get('p', 0)),  # 가격 (호환성)
                            "v": crypto_data.get('v', 0),  # 거래량
                            "timestamp": crypto_data.get('t', 0)
                        })
                
                # 통합 데이터 생성
                market_data = {
                    "type": "market_update",
                    "data": {
                        "stocks": stocks_data,
                        "cryptos": cryptos_data
                    },
                    "timestamp": int(time.time() * 1000)
                }
                
                await manager.broadcast(market_data)
                logger.info(f"Broadcasted market data to {len(manager.active_connections)} clients - {len(stocks_data)} stocks, {len(cryptos_data)} cryptos")
            
            # 10초 대기
            await asyncio.sleep(10)
            
        except asyncio.CancelledError:
            logger.info("Background broadcast task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in broadcast task: {e}")
            await asyncio.sleep(10)  # 에러 시 10초 후 재시도

@router.get("/ws/main")
async def websocket_status():
    """WebSocket 연결 상태 확인 API"""
    return {
        "active_connections": len(manager.active_connections),
        "is_broadcasting": is_broadcasting,
        "status": "active" if manager.active_connections else "idle"
    }

@router.get("/ws/stocks/status")
async def stocks_websocket_status():
    """주식 WebSocket 연결 상태 확인 API"""
    return {
        "endpoint": "/ws/stocks",
        "description": "주식 개별 심볼 WebSocket",
        "active_connections": len(manager.active_connections),
        "status": "ready"
    }

@router.get("/ws/crypto/status")
async def crypto_websocket_status():
    """암호화폐 WebSocket 연결 상태 확인 API"""
    from stock.backend.services.stock_service import get_crypto_statistics
    crypto_stats = get_crypto_statistics()
    
    return {
        "endpoint": "/ws/crypto",
        "description": "암호화폐 개별 심볼 WebSocket",
        "active_connections": len(manager.active_connections),
        "supported_symbols": crypto_stats.get("crypto_symbols", []),
        "thread_running": crypto_stats.get("thread_running", False),
        "status": "ready"
    }

@router.websocket("/ws/stocks")
async def websocket_stocks_endpoint(websocket: WebSocket, symbol: str = Query(...)):
    """개별 주식 심볼용 WebSocket 엔드포인트"""
    await manager.connect(websocket)
    logger.info(f"주식 WebSocket 연결: {symbol}")
    
    try:
        # 연결 즉시 주식 데이터 전송
        from stock.backend.services.stock_service import get_cached_stock_data
        stock_data = get_cached_stock_data(symbol)
        
        if stock_data:
            formatted_data = {
                "type": "stock_update",
                "data": [{
                    "s": symbol,
                    "p": str(stock_data.get('c', 0)),
                    "v": str(stock_data.get('v', 0)),
                    "t": int(stock_data.get('t', 0))
                }]
            }
            await manager.send_personal_message(formatted_data, websocket)
            logger.info(f"주식 데이터 전송 완료: {symbol}")
        
        # 주기적 업데이트 루프
        while True:
            await asyncio.sleep(10)  # 10초마다 업데이트
            
            # 최신 데이터 전송
            updated_data = get_cached_stock_data(symbol)
            if updated_data:
                formatted_data = {
                    "type": "stock_update",
                    "data": [{
                        "s": symbol,
                        "p": str(updated_data.get('c', 0)),
                        "v": str(updated_data.get('v', 0)),
                        "t": int(updated_data.get('t', 0))
                    }]
                }
                await manager.send_personal_message(formatted_data, websocket)
                logger.debug(f"주식 업데이트 전송: {symbol} - ${updated_data.get('c', 0)}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"주식 WebSocket 연결 해제: {symbol}")

@router.websocket("/ws/crypto")
async def websocket_crypto_endpoint(websocket: WebSocket, symbol: str = Query(...)):
    """암호화폐용 WebSocket 엔드포인트"""
    await manager.connect(websocket)
    logger.info(f"암호화폐 WebSocket 연결: {symbol}")
    
    try:
        # 연결 즉시 암호화폐 데이터 전송
        from stock.backend.services.stock_service import get_cached_crypto_data
        crypto_data = get_cached_crypto_data(symbol.upper())
        
        if crypto_data:
            formatted_data = {
                "type": "crypto_update",
                "data": [{
                    "s": crypto_data.get('s', ''),
                    "p": crypto_data.get('p', '0'),
                    "v": crypto_data.get('v', '0'),
                    "t": crypto_data.get('t', 0)
                }]
            }
            await manager.send_personal_message(formatted_data, websocket)
            logger.info(f"암호화폐 데이터 전송 완료: {symbol}")
        
        # 주기적 업데이트 루프
        while True:
            await asyncio.sleep(5)  # 5초마다 업데이트 (암호화폐는 더 빈번)
            
            # 최신 데이터 전송
            updated_data = get_cached_crypto_data(symbol.upper())
            if updated_data:
                formatted_data = {
                    "type": "crypto_update",
                    "data": [{
                        "s": updated_data.get('s', ''),
                        "p": updated_data.get('p', '0'),
                        "v": updated_data.get('v', '0'),
                        "t": updated_data.get('t', 0)
                    }]
                }
                await manager.send_personal_message(formatted_data, websocket)
                logger.debug(f"암호화폐 업데이트 전송: {symbol} - ${updated_data.get('p', '0')}")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"암호화폐 WebSocket 연결 해제: {symbol}")
