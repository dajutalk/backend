import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from stock.backend.websocket_manager import manager
from stock.backend.data_service import DataService
from stock.backend.database import get_db
import logging
import json
import time

logger = logging.getLogger(__name__)

router = APIRouter()

# 백그라운드 태스크 상태 관리
background_task = None
is_broadcasting = False

async def send_market_data_from_db(websocket: WebSocket, db: Session = None):
    """📊 DB에서 최근 30개 데이터를 가져와서 전송 - 개선된 버전"""
    if db is None:
        logger.warning("⚠️ DB 세션이 없어서 캐시된 데이터 사용")
        await send_cached_market_data(websocket)
        return
        
    try:
        from stock.backend.database.models import StockQuote, CryptoQuote
        from stock.backend.services.stock_service import TOP_10_CRYPTOS
        from sqlalchemy import desc
        
        # 🏢 주식 데이터 수집 (DB 우선, 캐시 fallback)
        stock_symbols = [
            "NVDA", "TSLA", "PLTR", "INTC", "AAPL", "BAC", "AMZN", "AMD", "GOOG", "MSFT",
            "META", "AVGO", "NFLX", "COST", "UNH", "MSTR", "LLY", "CRM", "V", "REGN",
            "APP", "WMT", "XOM", "MRVL", "ORCL", "JPM", "TXN", "ZS", "NOW", "MA",
            "IBM", "UBER", "JNJ", "AMAT", "HOOD", "ADI", "GE", "MU", "PANW",
            "INTU", "ABBV", "PG", "DELL", "CRWD", "SPOT", "LIN", "KO", "TMUS", "QCOM", "F"
        ]
        stocks_data = []
        
        logger.info(f"📈 주식 데이터 조회 시작 - {len(stock_symbols)}개 심볼")
        
        for symbol in stock_symbols:
            try:
                # DB에서 해당 심볼의 최근 30개 레코드 조회
                recent_quotes = db.query(StockQuote)\
                    .filter(StockQuote.symbol == symbol)\
                    .order_by(desc(StockQuote.created_at))\
                    .limit(30)\
                    .all()
                
                if recent_quotes:
                    # 시간순으로 정렬 (오래된 것부터)
                    recent_quotes.reverse()
                    
                    # 📊 차트용 히스토리 데이터 (30개 포인트)
                    history_data = []
                    for i, quote in enumerate(recent_quotes):
                        history_data.append({
                            "time": i + 1,  # 1부터 30까지의 인덱스
                            "price": float(quote.c),
                            "timestamp": int(quote.created_at.timestamp() * 1000)
                        })
                    
                    # 변동폭과 변동률 계산
                    current_price = float(recent_quotes[-1].c)
                    change = float(recent_quotes[-1].d) if recent_quotes[-1].d else 0
                    change_percent = float(recent_quotes[-1].dp) if recent_quotes[-1].dp else 0
                    
                    # 🚀 프론트엔드가 기대하는 형식으로 데이터 구성
                    stock_item = {
                        "symbol": symbol,
                        "price": current_price,
                        "change": change,
                        "changePercent": change_percent,
                        "history": history_data,
                        "timestamp": int(recent_quotes[-1].created_at.timestamp() * 1000),
                        "data_source": "database",
                        "last_updated": recent_quotes[-1].created_at.isoformat()
                    }
                    
                    stocks_data.append(stock_item)
                    logger.debug(f"✅ DB: {symbol} ${current_price} ({change:+.2f}, {change_percent:+.2f}%)")
                
                else:
                    # 📋 DB에 없으면 캐시에서 가져오기
                    from stock.backend.services.stock_service import get_cached_stock_data
                    cached_data = get_cached_stock_data(symbol)
                    
                    if cached_data:
                        current_price = cached_data.get('c', 0)
                        history_data = []
                        for i in range(30):
                            variation = current_price * 0.001 * (i - 15)  # ±1.5% 변동
                            history_data.append({
                                "time": i + 1,
                                "price": current_price + variation,
                                "timestamp": int(time.time() * 1000)
                            })
                        
                        stock_item = {
                            "symbol": symbol,
                            "price": current_price,
                            "change": cached_data.get('d', 0),
                            "changePercent": cached_data.get('dp', 0),
                            "history": history_data,
                            "timestamp": int(time.time() * 1000),
                            "data_source": "cache_fallback",
                            "cache_age": cached_data.get('_cache_age', 0)
                        }
                        stocks_data.append(stock_item)
                        logger.debug(f"📋 캐시: {symbol} ${current_price}")
                    
            except Exception as e:
                logger.error(f"❌ 주식 {symbol} 처리 오류: {e}")
                continue
        
        # 💰 암호화폐 데이터 수집 (DB 우선)
        cryptos_data = []
        logger.info(f"💰 암호화폐 데이터 조회 시작 - {len(TOP_10_CRYPTOS)}개 심볼")
        
        for symbol in TOP_10_CRYPTOS:
            try:
                recent_crypto_quotes = db.query(CryptoQuote)\
                    .filter(CryptoQuote.symbol == symbol)\
                    .order_by(desc(CryptoQuote.created_at))\
                    .limit(30)\
                    .all()
                
                if recent_crypto_quotes:
                    recent_crypto_quotes.reverse()
                    
                    # 📊 차트용 히스토리 데이터 (30개 포인트)
                    history_data = []
                    for i, quote in enumerate(recent_crypto_quotes):
                        history_data.append({
                            "time": i + 1,
                            "price": float(quote.p),
                            "timestamp": int(quote.created_at.timestamp() * 1000)
                        })
                    
                    # 🚀 프론트엔드가 기대하는 형식으로 데이터 구성
                    crypto_item = {
                        "symbol": symbol,
                        "price": float(recent_crypto_quotes[-1].p),
                        "change": 0,  # 암호화폐는 변동폭 계산 필요시 추가
                        "changePercent": 0,
                        "history": history_data,
                        "timestamp": int(recent_crypto_quotes[-1].created_at.timestamp() * 1000),
                        "data_source": "database",
                        "last_updated": recent_crypto_quotes[-1].created_at.isoformat()
                    }

                    cryptos_data.append(crypto_item)
                    logger.debug(f"✅ DB: {symbol} ${float(recent_crypto_quotes[-1].p)}")
                else:
                    # 📋 DB에 없으면 캐시에서 가져오기
                    from stock.backend.services.stock_service import get_cached_crypto_data
                    cached_data = get_cached_crypto_data(symbol)
                    
                    if cached_data:
                        current_price = float(cached_data.get('p', 0))
                        history_data = []
                        for i in range(30):
                            variation = current_price * 0.001 * (i - 15)
                            history_data.append({
                                "time": i + 1,
                                "price": current_price + variation,
                                "timestamp": int(time.time() * 1000)
                            })
                        
                        crypto_item = {
                            "symbol": symbol,
                            "price": current_price,
                            "change": 0,
                            "changePercent": 0,
                            "history": history_data,
                            "timestamp": int(time.time() * 1000),
                            "data_source": "cache_fallback",
                            "cache_age": cached_data.get('_cache_age', 0)
                        }
                        cryptos_data.append(crypto_item)
                        logger.debug(f"📋 캐시: {symbol} ${current_price}")
                    
            except Exception as e:
                logger.error(f"❌ 암호화폐 {symbol} 처리 오류: {e}")
                continue
        
        # 🚀 프론트엔드가 기대하는 형식으로 데이터 전송
        market_data = {
            "type": "market_update",
            "data": {
                "stocks": stocks_data,
                "cryptos": cryptos_data
            },
            "timestamp": int(time.time() * 1000),
            "stats": {
                "stocks_from_db": len([s for s in stocks_data if s.get("data_source") == "database"]),
                "stocks_from_cache": len([s for s in stocks_data if s.get("data_source") == "cache_fallback"]),
                "cryptos_from_db": len([c for c in cryptos_data if c.get("data_source") == "database"]),
                "cryptos_from_cache": len([c for c in cryptos_data if c.get("data_source") == "cache_fallback"]),
                "total_stocks": len(stocks_data),
                "total_cryptos": len(cryptos_data)
            },
            "message": f"📊 DB+캐시 혼합: 주식 {len(stocks_data)}개, 암호화폐 {len(cryptos_data)}개"
        }
        
        await manager.send_personal_message(market_data, websocket)
        
        # 📈 통계 로깅
        db_stocks = len([s for s in stocks_data if s.get("data_source") == "database"])
        cache_stocks = len([s for s in stocks_data if s.get("data_source") == "cache_fallback"])
        db_cryptos = len([c for c in cryptos_data if c.get("data_source") == "database"])
        cache_cryptos = len([c for c in cryptos_data if c.get("data_source") == "cache_fallback"])
        
        logger.info(f"✅ 📊 데이터 전송 완료:")
        logger.info(f"   주식: DB {db_stocks}개 + 캐시 {cache_stocks}개 = 총 {len(stocks_data)}개")
        logger.info(f"   암호화폐: DB {db_cryptos}개 + 캐시 {cache_cryptos}개 = 총 {len(cryptos_data)}개")
        
    except Exception as e:
        logger.error(f"❌ DB에서 데이터 조회 오류: {e}")
        import traceback
        logger.error(f"❌ 상세 스택 트레이스:\n{traceback.format_exc()}")
        await send_cached_market_data(websocket)

async def send_cached_market_data(websocket: WebSocket):
    """캐시된 데이터를 전송 (DB 연결 실패 시 fallback)"""
    try:
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
                # 히스토리가 없으므로 현재 가격으로 30개 포인트 생성
                history_data = []
                current_price = stock_data.get('c', 0)
                for i in range(30):
                    # 약간의 랜덤 변동을 주어 차트가 보이도록 함
                    variation = current_price * 0.001 * (i - 15)  # ±1.5% 변동
                    history_data.append({
                        "time": i + 1,
                        "price": current_price + variation
                        # volume 필드 제거
                    })
                
                stocks_data.append({
                    "symbol": symbol,
                    "price": current_price,
                    "change": stock_data.get('d', 0),
                    "changePercent": stock_data.get('dp', 0),
                    # volume 필드 제거
                    "history": history_data,
                    "timestamp": int(time.time() * 1000),
                    "data_source": "cache"
                })
        
        # 암호화폐 데이터 수집
        cryptos_data = []
        for symbol in TOP_10_CRYPTOS:
            crypto_data = get_cached_crypto_data(symbol)
            if crypto_data:
                # 히스토리가 없으므로 현재 가격으로 30개 포인트 생성
                history_data = []
                current_price = float(crypto_data.get('p', 0))
                for i in range(30):
                    # 약간의 랜덤 변동을 주어 차트가 보이도록 함
                    variation = current_price * 0.001 * (i - 15)  # ±1.5% 변동
                    history_data.append({
                        "time": i + 1,
                        "price": current_price + variation
                        # volume 필드 제거
                    })
                
                cryptos_data.append({
                    "symbol": symbol,
                    "price": current_price,
                    "change": 0,
                    "changePercent": 0,
                    # volume 필드 제거
                    "history": history_data,
                    "timestamp": int(time.time() * 1000),
                    "data_source": "cache"
                })
        
        # 데이터 전송
        market_data = {
            "type": "market_update",
            "data": {
                "stocks": stocks_data,
                "cryptos": cryptos_data
            },
            "timestamp": int(time.time() * 1000),
            "data_source": "cache",
            "message": f"캐시에서 {len(stocks_data)}개 주식, {len(cryptos_data)}개 암호화폐 데이터 전송"
        }
        
        await manager.send_personal_message(market_data, websocket)
        logger.info(f"Cache market data sent - {len(stocks_data)} stocks, {len(cryptos_data)} cryptos")
        
    except Exception as e:
        logger.error(f"❌ 캐시 데이터 전송 오류: {e}")

@router.websocket("/ws/main")
async def websocket_endpoint(websocket: WebSocket):
    """메인 WebSocket 엔드포인트 - DB 기반"""
    global background_task, is_broadcasting
    
    await manager.connect(websocket)
    logger.info(f"✅ WebSocket 클라이언트 연결됨. 총 연결: {len(manager.active_connections)}")
    
    # 첫 번째 클라이언트 연결 시 백그라운드 브로드캐스트 시작
    if not is_broadcasting and len(manager.active_connections) == 1:
        background_task = asyncio.create_task(broadcast_market_data())
        is_broadcasting = True
        logger.info("Started background broadcasting task")
    
    try:
        # 연결 즉시 데이터 전송 - DB 세션 직접 생성
        from stock.backend.database import SessionLocal
        db = SessionLocal()
        try:
            await send_market_data_from_db(websocket, db)
        finally:
            db.close()
        
        # 클라이언트로부터 메시지 대기 (연결 유지)
        while True:
            try:
                message = await websocket.receive_text()
                logger.info(f"Received message from client: {message}")
                
                # 클라이언트 요청에 따른 즉시 데이터 전송
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
        if len(manager.active_connections) == 0 and background_task:
            background_task.cancel()
            is_broadcasting = False
            logger.info("Stopped background broadcasting task")

async def broadcast_market_data():
    """DB에서 최근 30개 데이터를 10초마다 모든 클라이언트에게 브로드캐스트"""
    while True:
        try:
            if manager.active_connections:
                from stock.backend.database import SessionLocal
                db = SessionLocal()
                try:
                    # 모든 연결된 클라이언트에게 데이터 전송
                    for websocket in manager.active_connections.copy():
                        try:
                            await send_market_data_from_db(websocket, db)
                        except Exception as e:
                            logger.error(f"❌ 클라이언트 전송 오류: {e}")
                            # 연결이 끊어진 클라이언트 제거
                            manager.disconnect(websocket)
                finally:
                    db.close()
            
            # 10초 대기
            await asyncio.sleep(10)
            
        except asyncio.CancelledError:
            logger.info("Background broadcast task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in broadcast task: {e}")
            await asyncio.sleep(10)

@router.get("/ws/stocks/status")
async def stocks_websocket_status():
    """주식 WebSocket 연결 상태 확인 API"""
    return {
        "endpoint": "/ws/stocks",
        "description": "주식 개별 심볼 WebSocket (DB 기반)",
        "active_connections": len(manager.active_connections),
        "data_source": "database",
        "status": "ready"
    }

@router.get("/ws/crypto/status")
async def crypto_websocket_status():
    """암호화폐 WebSocket 연결 상태 확인 API"""
    from stock.backend.services.stock_service import get_crypto_statistics
    crypto_stats = get_crypto_statistics()
    
    return {
        "endpoint": "/ws/crypto",
        "description": "암호화폐 개별 심볼 WebSocket (DB 기반)",
        "active_connections": len(manager.active_connections),
        "supported_symbols": crypto_stats.get("crypto_symbols", []),
        "thread_running": crypto_stats.get("thread_running", False),
        "data_source": "database",
        "status": "ready"
    }

@router.websocket("/ws/stocks")
async def websocket_stocks_endpoint(websocket: WebSocket, symbol: str = Query(...), db: Session = Depends(get_db)):
    """개별 주식 심볼용 WebSocket 엔드포인트 - DB에서 최근 30개 데이터"""
    await manager.connect(websocket)
    logger.info(f"주식 WebSocket 연결: {symbol} (DB 모드)")
    
    try:
        from stock.backend.models import StockQuote
        from sqlalchemy import desc
        
        # 연속적으로 DB에서 데이터 전송
        while True:
            # DB에서 해당 심볼의 최근 30개 레코드 조회
            recent_quotes = db.query(StockQuote)\
                .filter(StockQuote.symbol == symbol)\
                .order_by(desc(StockQuote.created_at))\
                .limit(30)\
                .all()
            
            if recent_quotes:
                recent_quotes.reverse()
                
                stock_history = []
                for quote in recent_quotes:
                    stock_history.append({
                        "time": quote.created_at.strftime("%H:%M:%S"),
                        "price": float(quote.c),
                        # volume 필드 제거
                        "timestamp": int(quote.created_at.timestamp() * 1000)
                    })
                
                formatted_data = {
                    "type": "stock_update",
                    "data": {
                        "symbol": symbol,
                        "history": stock_history,
                        "current_price": float(recent_quotes[-1].c),
                        "last_update": recent_quotes[-1].created_at.isoformat(),
                        "data_source": "database"
                    }
                }
                await manager.send_personal_message(formatted_data, websocket)
                logger.debug(f"주식 DB 업데이트 전송: {symbol} - {len(stock_history)}개 히스토리")
            else:
                # DB에 데이터가 없는 경우 빈 응답
                formatted_data = {
                    "type": "stock_update",
                    "data": {
                        "symbol": symbol,
                        "history": [],
                        "current_price": 0,
                        "last_update": None,
                        "data_source": "database",
                        "message": "DB에 데이터가 없습니다"
                    }
                }
                await manager.send_personal_message(formatted_data, websocket)
            
            # 2초 간격으로 업데이트
            await asyncio.sleep(2.0)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"주식 WebSocket 연결 해제: {symbol}")

@router.websocket("/ws/crypto")
async def websocket_crypto_endpoint(websocket: WebSocket, symbol: str = Query(...), db: Session = Depends(get_db)):
    """암호화폐용 WebSocket 엔드포인트 - DB에서 최근 30개 데이터"""
    await manager.connect(websocket)
    logger.info(f"암호화폐 WebSocket 연결: {symbol} (DB 모드)")
    
    try:
        from stock.backend.models import CryptoQuote
        from sqlalchemy import desc
        
        # 연속적으로 DB에서 데이터 전송
        while True:
            # DB에서 해당 암호화폐의 최근 30개 레코드 조회
            recent_crypto_quotes = db.query(CryptoQuote)\
                .filter(CryptoQuote.symbol == symbol.upper())\
                .order_by(desc(CryptoQuote.created_at))\
                .limit(30)\
                .all()
            
            if recent_crypto_quotes:
                recent_crypto_quotes.reverse()
                
                crypto_history = []
                for quote in recent_crypto_quotes:
                    crypto_history.append({
                        "time": quote.created_at.strftime("%H:%M:%S"),
                        "price": float(quote.p),
                        # volume 필드 제거
                        "timestamp": int(quote.created_at.timestamp() * 1000)
                    })
                
                formatted_data = {
                    "type": "crypto_update",
                    "data": {
                        "symbol": symbol.upper(),
                        "history": crypto_history,
                        "current_price": float(recent_crypto_quotes[-1].p),
                        "last_update": recent_crypto_quotes[-1].created_at.isoformat(),
                        "data_source": "database"
                    }
                }
                await manager.send_personal_message(formatted_data, websocket)
                logger.debug(f"암호화폐 DB 업데이트 전송: {symbol} - {len(crypto_history)}개 히스토리")
            else:
                # DB에 데이터가 없는 경우 빈 응답
                formatted_data = {
                    "type": "crypto_update",
                    "data": {
                        "symbol": symbol.upper(),
                        "history": [],
                        "current_price": 0,
                        "last_update": None,
                        "data_source": "database",
                        "message": "DB에 데이터가 없습니다"
                    }
                }
                await manager.send_personal_message(formatted_data, websocket)
            
            # 1초 간격으로 업데이트 (암호화폐는 더 빠르게)
            await asyncio.sleep(1.0)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"암호화폐 WebSocket 연결 해제: {symbol}")
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

async def send_market_data_from_db(websocket: WebSocket, db: Session = None):
    """DB에서 최근 30개 데이터를 가져와서 전송"""
    if db is None:
        logger.warning("⚠️ DB 세션이 없어서 캐시된 데이터 사용")
        await send_cached_market_data(websocket)
        return
        
    try:
        from stock.backend.models import StockQuote, CryptoQuote
        from stock.backend.services.stock_service import TOP_10_CRYPTOS
        from sqlalchemy import desc
        
        # 주요 주식 데이터 수집 (DB에서 최근 30개)
        stock_symbols = [
            "NVDA", "TSLA", "PLTR", "INTC", "AAPL", "BAC", "AMZN", "AMD", "GOOG", "MSFT",
            "META", "AVGO", "NFLX", "COST", "UNH", "MSTR", "LLY", "CRM", "V", "REGN",
            "APP", "WMT", "XOM", "MRVL", "ORCL", "JPM", "TXN", "ZS", "NOW", "MA",
            "IBM", "UBER", "JNJ", "AMAT", "HOOD", "ADI", "GE", "MU", "PANW",
            "INTU", "ABBV", "PG", "DELL", "CRWD", "SPOT", "LIN", "KO", "TMUS", "QCOM", "F"
        ]
        stocks_data = []
        
        logger.info(f"🔍 주식 데이터 조회 시작 - {len(stock_symbols)}개 심볼")
        
        for symbol in stock_symbols:
            try:
                # DB에서 해당 심볼의 최근 30개 레코드 조회
                recent_quotes = db.query(StockQuote)\
                    .filter(StockQuote.symbol == symbol)\
                    .order_by(desc(StockQuote.created_at))\
                    .limit(30)\
                    .all()
                
                logger.info(f"📊 {symbol}: {len(recent_quotes)}개 레코드 발견")  # debug -> info로 변경
                
                if recent_quotes:
                    # 시간순으로 정렬 (오래된 것부터)
                    recent_quotes.reverse()
                    
                    # 차트용 히스토리 데이터 (30개 포인트)
                    history_data = []
                    for i, quote in enumerate(recent_quotes):
                        history_data.append({
                            "time": i + 1,  # 1부터 30까지의 인덱스
                            "price": float(quote.c)
                            # volume 필드 제거
                        })
                    
                    # 변동폭과 변동률 계산
                    current_price = float(recent_quotes[-1].c)
                    change = float(recent_quotes[-1].d) if recent_quotes[-1].d else 0
                    change_percent = float(recent_quotes[-1].dp) if recent_quotes[-1].dp else 0
                    
                    # 프론트엔드가 기대하는 형식으로 데이터 구성
                    stock_item = {
                        "symbol": symbol,
                        "price": current_price,
                        "change": change,
                        "changePercent": change_percent,
                        # volume 필드 제거
                        "history": history_data,
                        "timestamp": int(recent_quotes[-1].created_at.timestamp() * 1000),
                        "data_source": "database"
                    }
                    
                    stocks_data.append(stock_item)
                    logger.info(f"✅ {symbol} 데이터 추가: ${current_price} ({change:+.2f}, {change_percent:+.2f}%)")
                else:
                    logger.info(f"⚠️ {symbol}: DB에 데이터 없음")
                    
            except Exception as e:
                logger.error(f"❌ 주식 {symbol} 조회 오류: {e}")
                import traceback
                logger.error(f"❌ {symbol} 상세 오류: {traceback.format_exc()}")
                continue
        
        logger.info(f"📈 주식 데이터 수집 완료: {len(stocks_data)}개")
        
        # 암호화폐 데이터 수집 (DB에서 최근 30개)
        cryptos_data = []
        logger.info(f"🔍 암호화폐 데이터 조회 시작 - {len(TOP_10_CRYPTOS)}개 심볼")
        
        for symbol in TOP_10_CRYPTOS:
            try:
                recent_crypto_quotes = db.query(CryptoQuote)\
                    .filter(CryptoQuote.symbol == symbol)\
                    .order_by(desc(CryptoQuote.created_at))\
                    .limit(30)\
                    .all()
                
                logger.debug(f"💰 {symbol}: {len(recent_crypto_quotes)}개 레코드 발견")
                
                if recent_crypto_quotes:
                    recent_crypto_quotes.reverse()
                    
                    # 차트용 히스토리 데이터 (30개 포인트)
                    history_data = []
                    for i, quote in enumerate(recent_crypto_quotes):
                        history_data.append({
                            "time": i + 1,  # 1부터 30까지의 인덱스
                            "price": float(quote.p)
                            # volume 필드 제거
                        })
                    
                    # 프론트엔드가 기대하는 형식으로 데이터 구성
                    crypto_item = {
                        "symbol": symbol,
                        "price": float(recent_crypto_quotes[-1].p),
                        "change": 0,  # 암호화폐는 변동폭 데이터가 별도로 없음
                        "changePercent": 0,  # 변동률 계산 필요시 추가
                        # volume 필드 제거
                        "history": history_data,
                        "timestamp": int(recent_crypto_quotes[-1].created_at.timestamp() * 1000),
                        "data_source": "database"
                    }

                    cryptos_data.append(crypto_item)
                    logger.debug(f"✅ {symbol} 데이터 추가: ${float(recent_crypto_quotes[-1].p)}")
                else:
                    logger.debug(f"⚠️ {symbol}: DB에 데이터 없음")
                    
            except Exception as e:
                logger.error(f"❌ 암호화폐 {symbol} 조회 오류: {e}")
                continue
        
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
        logger.info(f"✅ DB market data sent - {len(stocks_data)} stocks with history, {len(cryptos_data)} cryptos with history")
        
    except Exception as e:
        logger.error(f"❌ DB에서 데이터 조회 오류: {e}")
        import traceback
        logger.error(f"❌ 상세 스택 트레이스:\n{traceback.format_exc()}")
        await send_cached_market_data(websocket)

async def send_cached_market_data(websocket: WebSocket):
    """캐시된 데이터를 전송 (DB 연결 실패 시 fallback)"""
    try:
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
                # 히스토리가 없으므로 현재 가격으로 30개 포인트 생성
                history_data = []
                current_price = stock_data.get('c', 0)
                for i in range(30):
                    # 약간의 랜덤 변동을 주어 차트가 보이도록 함
                    variation = current_price * 0.001 * (i - 15)  # ±1.5% 변동
                    history_data.append({
                        "time": i + 1,
                        "price": current_price + variation
                        # volume 필드 제거
                    })
                
                stocks_data.append({
                    "symbol": symbol,
                    "price": current_price,
                    "change": stock_data.get('d', 0),
                    "changePercent": stock_data.get('dp', 0),
                    # volume 필드 제거
                    "history": history_data,
                    "timestamp": int(time.time() * 1000),
                    "data_source": "cache"
                })
        
        # 암호화폐 데이터 수집
        cryptos_data = []
        for symbol in TOP_10_CRYPTOS:
            crypto_data = get_cached_crypto_data(symbol)
            if crypto_data:
                # 히스토리가 없으므로 현재 가격으로 30개 포인트 생성
                history_data = []
                current_price = float(crypto_data.get('p', 0))
                for i in range(30):
                    # 약간의 랜덤 변동을 주어 차트가 보이도록 함
                    variation = current_price * 0.001 * (i - 15)  # ±1.5% 변동
                    history_data.append({
                        "time": i + 1,
                        "price": current_price + variation
                        # volume 필드 제거
                    })
                
                cryptos_data.append({
                    "symbol": symbol,
                    "price": current_price,
                    "change": 0,
                    "changePercent": 0,
                    # volume 필드 제거
                    "history": history_data,
                    "timestamp": int(time.time() * 1000),
                    "data_source": "cache"
                })
        
        # 데이터 전송
        market_data = {
            "type": "market_update",
            "data": {
                "stocks": stocks_data,
                "cryptos": cryptos_data
            },
            "timestamp": int(time.time() * 1000),
            "data_source": "cache",
            "message": f"캐시에서 {len(stocks_data)}개 주식, {len(cryptos_data)}개 암호화폐 데이터 전송"
        }
        
        await manager.send_personal_message(market_data, websocket)
        logger.info(f"Cache market data sent - {len(stocks_data)} stocks, {len(cryptos_data)} cryptos")
        
    except Exception as e:
        logger.error(f"❌ 캐시 데이터 전송 오류: {e}")

@router.websocket("/ws/main")
async def websocket_endpoint(websocket: WebSocket):
    """메인 WebSocket 엔드포인트 - DB 기반"""
    global background_task, is_broadcasting
    
    await manager.connect(websocket)
    logger.info(f"✅ WebSocket 클라이언트 연결됨. 총 연결: {len(manager.active_connections)}")
    
    # 첫 번째 클라이언트 연결 시 백그라운드 브로드캐스트 시작
    if not is_broadcasting and len(manager.active_connections) == 1:
        background_task = asyncio.create_task(broadcast_market_data())
        is_broadcasting = True
        logger.info("Started background broadcasting task")
    
    try:
        # 연결 즉시 데이터 전송 - DB 세션 직접 생성
        from stock.backend.database import SessionLocal
        db = SessionLocal()
        try:
            await send_market_data_from_db(websocket, db)
        finally:
            db.close()
        
        # 클라이언트로부터 메시지 대기 (연결 유지)
        while True:
            try:
                message = await websocket.receive_text()
                logger.info(f"Received message from client: {message}")
                
                # 클라이언트 요청에 따른 즉시 데이터 전송
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
        if len(manager.active_connections) == 0 and background_task:
            background_task.cancel()
            is_broadcasting = False
            logger.info("Stopped background broadcasting task")

async def broadcast_market_data():
    """DB에서 최근 30개 데이터를 10초마다 모든 클라이언트에게 브로드캐스트"""
    while True:
        try:
            if manager.active_connections:
                from stock.backend.database import SessionLocal
                db = SessionLocal()
                try:
                    # 모든 연결된 클라이언트에게 데이터 전송
                    for websocket in manager.active_connections.copy():
                        try:
                            await send_market_data_from_db(websocket, db)
                        except Exception as e:
                            logger.error(f"❌ 클라이언트 전송 오류: {e}")
                            # 연결이 끊어진 클라이언트 제거
                            manager.disconnect(websocket)
                finally:
                    db.close()
            
            # 10초 대기
            await asyncio.sleep(10)
            
        except asyncio.CancelledError:
            logger.info("Background broadcast task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in broadcast task: {e}")
            await asyncio.sleep(10)

@router.get("/ws/stocks/status")
async def stocks_websocket_status():
    """주식 WebSocket 연결 상태 확인 API"""
    return {
        "endpoint": "/ws/stocks",
        "description": "주식 개별 심볼 WebSocket (DB 기반)",
        "active_connections": len(manager.active_connections),
        "data_source": "database",
        "status": "ready"
    }

@router.get("/ws/crypto/status")
async def crypto_websocket_status():
    """암호화폐 WebSocket 연결 상태 확인 API"""
    from stock.backend.services.stock_service import get_crypto_statistics
    crypto_stats = get_crypto_statistics()
    
    return {
        "endpoint": "/ws/crypto",
        "description": "암호화폐 개별 심볼 WebSocket (DB 기반)",
        "active_connections": len(manager.active_connections),
        "supported_symbols": crypto_stats.get("crypto_symbols", []),
        "thread_running": crypto_stats.get("thread_running", False),
        "data_source": "database",
        "status": "ready"
    }

@router.websocket("/ws/stocks")
async def websocket_stocks_endpoint(websocket: WebSocket, symbol: str = Query(...), db: Session = Depends(get_db)):
    """개별 주식 심볼용 WebSocket 엔드포인트 - DB에서 최근 30개 데이터"""
    await manager.connect(websocket)
    logger.info(f"주식 WebSocket 연결: {symbol} (DB 모드)")
    
    try:
        from stock.backend.models import StockQuote
        from sqlalchemy import desc
        
        # 연속적으로 DB에서 데이터 전송
        while True:
            # DB에서 해당 심볼의 최근 30개 레코드 조회
            recent_quotes = db.query(StockQuote)\
                .filter(StockQuote.symbol == symbol)\
                .order_by(desc(StockQuote.created_at))\
                .limit(30)\
                .all()
            
            if recent_quotes:
                recent_quotes.reverse()
                
                stock_history = []
                for quote in recent_quotes:
                    stock_history.append({
                        "time": quote.created_at.strftime("%H:%M:%S"),
                        "price": float(quote.c),
                        # volume 필드 제거
                        "timestamp": int(quote.created_at.timestamp() * 1000)
                    })
                
                formatted_data = {
                    "type": "stock_update",
                    "data": {
                        "symbol": symbol,
                        "history": stock_history,
                        "current_price": float(recent_quotes[-1].c),
                        "last_update": recent_quotes[-1].created_at.isoformat(),
                        "data_source": "database"
                    }
                }
                await manager.send_personal_message(formatted_data, websocket)
                logger.debug(f"주식 DB 업데이트 전송: {symbol} - {len(stock_history)}개 히스토리")
            else:
                # DB에 데이터가 없는 경우 빈 응답
                formatted_data = {
                    "type": "stock_update",
                    "data": {
                        "symbol": symbol,
                        "history": [],
                        "current_price": 0,
                        "last_update": None,
                        "data_source": "database",
                        "message": "DB에 데이터가 없습니다"
                    }
                }
                await manager.send_personal_message(formatted_data, websocket)
            
            # 2초 간격으로 업데이트
            await asyncio.sleep(2.0)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"주식 WebSocket 연결 해제: {symbol}")

@router.websocket("/ws/crypto")
async def websocket_crypto_endpoint(websocket: WebSocket, symbol: str = Query(...), db: Session = Depends(get_db)):
    """암호화폐용 WebSocket 엔드포인트 - DB에서 최근 30개 데이터"""
    await manager.connect(websocket)
    logger.info(f"암호화폐 WebSocket 연결: {symbol} (DB 모드)")
    
    try:
        from stock.backend.models import CryptoQuote
        from sqlalchemy import desc
        
        # 연속적으로 DB에서 데이터 전송
        while True:
            # DB에서 해당 암호화폐의 최근 30개 레코드 조회
            recent_crypto_quotes = db.query(CryptoQuote)\
                .filter(CryptoQuote.symbol == symbol.upper())\
                .order_by(desc(CryptoQuote.created_at))\
                .limit(30)\
                .all()
            
            if recent_crypto_quotes:
                recent_crypto_quotes.reverse()
                
                crypto_history = []
                for quote in recent_crypto_quotes:
                    crypto_history.append({
                        "time": quote.created_at.strftime("%H:%M:%S"),
                        "price": float(quote.p),
                        # volume 필드 제거
                        "timestamp": int(quote.created_at.timestamp() * 1000)
                    })
                
                formatted_data = {
                    "type": "crypto_update",
                    "data": {
                        "symbol": symbol.upper(),
                        "history": crypto_history,
                        "current_price": float(recent_crypto_quotes[-1].p),
                        "last_update": recent_crypto_quotes[-1].created_at.isoformat(),
                        "data_source": "database"
                    }
                }
                await manager.send_personal_message(formatted_data, websocket)
                logger.debug(f"암호화폐 DB 업데이트 전송: {symbol} - {len(crypto_history)}개 히스토리")
            else:
                # DB에 데이터가 없는 경우 빈 응답
                formatted_data = {
                    "type": "crypto_update",
                    "data": {
                        "symbol": symbol.upper(),
                        "history": [],
                        "current_price": 0,
                        "last_update": None,
                        "data_source": "database",
                        "message": "DB에 데이터가 없습니다"
                    }
                }
                await manager.send_personal_message(formatted_data, websocket)
            
            # 1초 간격으로 업데이트 (암호화폐는 더 빠르게)
            await asyncio.sleep(1.0)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"암호화폐 WebSocket 연결 해제: {symbol}")
