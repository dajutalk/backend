from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db, SessionLocal
from . import manager, stock_handler, crypto_handler
import asyncio
import logging
import time

logger = logging.getLogger(__name__)

router = APIRouter()

# 백그라운드 태스크 상태 관리
background_task = None
is_broadcasting = False

async def send_market_data_from_db(websocket: WebSocket, db: Session = None):
    """DB에서 최근 30개 데이터를 가져와서 전송"""
    if db is None:
        logger.warning("⚠️ DB 세션이 없어서 캐시된 데이터 사용")
        await send_cached_market_data(websocket)
        return
        
    try:
        # 주식 데이터 수집
        stocks_data = await stock_handler.get_stock_market_data(db)
        logger.info(f"📈 주식 데이터 수집 완료: {len(stocks_data)}개")
        
        # 암호화폐 데이터 수집
        cryptos_data = await crypto_handler.get_crypto_market_data(db)
        logger.info(f"💰 암호화폐 데이터 수집 완료: {len(cryptos_data)}개")
        
        # 프론트엔드가 기대하는 형식으로 데이터 전송
        market_data = {
            "type": "market_update",
            "data": {
                "stocks": stocks_data,
                "cryptos": cryptos_data
            },
            "timestamp": int(time.time() * 1000),
            "data_source": "database",
            "message": f"DB에서 {len(stocks_data)}개 주식, {len(cryptos_data)}개 암호화폐 데이터 전송"
        }
        
        await manager.send_personal_message(market_data, websocket)
        logger.info(f"✅ DB market data sent - {len(stocks_data)} stocks, {len(cryptos_data)} cryptos")
        
    except Exception as e:
        logger.error(f"❌ DB에서 데이터 조회 오류: {e}")
        await send_cached_market_data(websocket)

async def send_cached_market_data(websocket: WebSocket):
    """캐시된 데이터를 전송 (DB 연결 실패 시 fallback)"""
    try:
        # 캐시 데이터 로직 (기존 코드 유지)
        market_data = {
            "type": "market_update",
            "data": {
                "stocks": [],
                "cryptos": []
            },
            "timestamp": int(time.time() * 1000),
            "data_source": "cache",
            "message": "캐시 모드로 동작 중"
        }
        
        await manager.send_personal_message(market_data, websocket)
        logger.info("Cache market data sent")
        
    except Exception as e:
        logger.error(f"❌ 캐시 데이터 전송 오류: {e}")

@router.websocket("/ws/main")
async def websocket_endpoint(websocket: WebSocket):
    """메인 WebSocket 엔드포인트 - DB 기반"""
    global background_task, is_broadcasting
    
    await manager.connect(websocket)
    logger.info(f"✅ WebSocket 클라이언트 연결됨. 총 연결: {manager.get_connection_count()}")
    
    # 첫 번째 클라이언트 연결 시 백그라운드 브로드캐스트 시작
    if not is_broadcasting and manager.get_connection_count() == 1:
        background_task = asyncio.create_task(broadcast_market_data())
        is_broadcasting = True
        logger.info("Started background broadcasting task")
    
    try:
        # 연결 즉시 데이터 전송
        db = SessionLocal()
        try:
            await send_market_data_from_db(websocket, db)
        finally:
            db.close()
        
        # 클라이언트로부터 메시지 대기
        while True:
            try:
                message = await websocket.receive_text()
                logger.info(f"Received message from client: {message}")
                
                if message == "get_latest":
                    db = SessionLocal()
                    try:
                        await send_market_data_from_db(websocket, db)
                    finally:
                        db.close()
                    
            except WebSocketDisconnect:
                break

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected")
        
        # 모든 클라이언트가 연결 해제되면 백그라운드 태스크 중지
        if manager.get_connection_count() == 0 and background_task:
            background_task.cancel()
            is_broadcasting = False
            logger.info("Stopped background broadcasting task")

async def broadcast_market_data():
    """DB에서 최근 30개 데이터를 10초마다 모든 클라이언트에게 브로드캐스트"""
    while True:
        try:
            if manager.get_connection_count() > 0:
                db = SessionLocal()
                try:
                    # 모든 연결된 클라이언트에게 데이터 전송
                    for websocket in manager.active_connections.copy():
                        try:
                            await send_market_data_from_db(websocket, db)
                        except Exception as e:
                            logger.error(f"❌ 클라이언트 전송 오류: {e}")
                            manager.disconnect(websocket)
                finally:
                    db.close()
            
            await asyncio.sleep(10)
            
        except asyncio.CancelledError:
            logger.info("Background broadcast task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in broadcast task: {e}")
            await asyncio.sleep(10)

@router.websocket("/ws/stocks")
async def websocket_stocks_endpoint(websocket: WebSocket, symbol: str = Query(...), db: Session = Depends(get_db)):
    """개별 주식 심볼용 WebSocket 엔드포인트"""
    await manager.connect(websocket, {"type": "stock", "symbol": symbol})
    logger.info(f"주식 WebSocket 연결: {symbol}")
    
    try:
        await stock_handler.handle_stock_updates(websocket, symbol, db)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"주식 WebSocket 연결 해제: {symbol}")

@router.websocket("/ws/crypto")
async def websocket_crypto_endpoint(websocket: WebSocket, symbol: str = Query(...), db: Session = Depends(get_db)):
    """암호화폐용 WebSocket 엔드포인트"""
    await manager.connect(websocket, {"type": "crypto", "symbol": symbol})
    logger.info(f"암호화폐 WebSocket 연결: {symbol}")
    
    try:
        await crypto_handler.handle_crypto_updates(websocket, symbol, db)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"암호화폐 WebSocket 연결 해제: {symbol}")

@router.get("/ws/status")
async def websocket_status():
    """WebSocket 연결 상태 확인"""
    return {
        "active_connections": manager.get_connection_count(),
        "stock_connections": len(manager.get_connections_by_type("stock")),
        "crypto_connections": len(manager.get_connections_by_type("crypto")),
        "data_source": "database",
        "status": "ready"
    }
