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
async def get_stock_quote_endpoint(symbol: str = Query(...), save_to_db: bool = Query(default=True)):
    """
    주식 시세 조회 API - DB 저장 옵션 추가
    
    :param symbol: 주식 심볼
    :param save_to_db: DB 저장 여부 (기본값: True, 자동수집기에서는 False 사용)
    """
    if symbol.startswith("BINANCE:"):
        raise HTTPException(
            status_code=400, 
            detail="가상화폐는 /ws/stocks 웹소켓 엔드포인트를 통해 조회하세요"
        )
    
    # stock_service에서 캐시된 데이터 조회
    from stock.backend.services.stock_service import get_cached_stock_data, register_symbol
    from stock.backend.services.quote_service import quote_service
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
        
        response_data = {
            "symbol": symbol,
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
        
        # 📊 조건부 DB 저장
        if save_to_db and final_source == 'api':
            saved = quote_service.save_stock_quote(response_data)
            logger.info(f"💾 DB 저장: {symbol} {'성공' if saved else '실패'}")
        
        return response_data
    else:
        logger.error(f"❌ 데이터 없음: {symbol}")
        raise HTTPException(status_code=404, detail=f"심볼 '{symbol}'의 데이터를 찾을 수 없습니다")

# 📊 새로운 API 엔드포인트 추가
@rest_router.get("/history/{symbol}")
async def get_stock_history(symbol: str, hours: int = Query(default=24, description="조회할 시간 범위 (시간 단위)")):
    """주식 시세 이력 조회"""
    from stock.backend.services.quote_service import quote_service
    
    history = quote_service.get_quote_history(symbol, hours)
    return {
        "symbol": symbol,
        "hours": hours,
        "count": len(history),
        "data": [
            {
                "c": quote.c,
                "d": quote.d,
                "dp": quote.dp,
                "h": quote.h,
                "l": quote.l,
                "o": quote.o,
                "pc": quote.pc,
                "created_at": quote.created_at.isoformat()
            } for quote in history
        ]
    }

@rest_router.get("/statistics/{symbol}")
async def get_stock_statistics(symbol: str):
    """특정 심볼의 통계 정보 조회"""
    from stock.backend.services.quote_service import quote_service
    
    stats = quote_service.get_quote_statistics(symbol)
    if not stats:
        raise HTTPException(status_code=404, detail=f"심볼 '{symbol}'의 데이터를 찾을 수 없습니다")
    
    return stats

@rest_router.get("/symbols")
async def get_stored_symbols():
    """저장된 모든 심볼 목록 조회"""
    from stock.backend.services.quote_service import quote_service
    
    symbols = quote_service.get_all_symbols()
    return {
        "total": len(symbols),
        "symbols": symbols
    }

@rest_router.get("/scheduler/status")
async def get_scheduler_status():
    """스케줄러 상태 조회"""
    from stock.backend.services.scheduler_service import stock_scheduler
    
    status = stock_scheduler.get_status()
    return {
        "scheduler_status": status,
        "message": "스케줄러가 실행 중입니다" if status["is_running"] else "스케줄러가 중지되었습니다"
    }

@rest_router.post("/scheduler/start")
async def start_scheduler():
    """스케줄러 수동 시작"""
    from stock.backend.services.scheduler_service import stock_scheduler
    
    if stock_scheduler.is_running:
        return {"message": "스케줄러가 이미 실행 중입니다"}
    
    stock_scheduler.start_scheduler()
    return {"message": "스케줄러가 시작되었습니다"}

@rest_router.post("/scheduler/stop")
async def stop_scheduler():
    """스케줄러 수동 중지"""
    from stock.backend.services.scheduler_service import stock_scheduler
    
    if not stock_scheduler.is_running:
        return {"message": "스케줄러가 이미 중지되었습니다"}
    
    stock_scheduler.stop_scheduler()
    return {"message": "스케줄러가 중지되었습니다"}

@rest_router.get("/scheduler/symbols")
async def get_monitored_symbols():
    """모니터링 중인 심볼 목록 조회"""
    from stock.backend.services.scheduler_service import MOST_ACTIVE_STOCKS
    
    return {
        "total": len(MOST_ACTIVE_STOCKS),
        "symbols": MOST_ACTIVE_STOCKS
    }

@rest_router.get("/collector/status")
async def get_collector_status():
    """자동 수집기 상태 조회"""
    from stock.backend.services.auto_collector import auto_collector
    
    status = auto_collector.get_status()
    return {
        "collector_status": status,
        "message": "자동 수집기가 실행 중입니다" if status["is_running"] else "자동 수집기가 중지되었습니다"
    }

@rest_router.post("/collector/start")
async def start_collector():
    """자동 수집기 수동 시작"""
    from stock.backend.services.auto_collector import auto_collector
    
    if auto_collector.is_running:
        return {"message": "자동 수집기가 이미 실행 중입니다"}
    
    auto_collector.start_collector()
    return {"message": "자동 수집기가 시작되었습니다"}

@rest_router.post("/collector/stop")
async def stop_collector():
    """자동 수집기 수동 중지"""
    from stock.backend.services.auto_collector import auto_collector
    
    if not auto_collector.is_running:
        return {"message": "자동 수집기가 이미 중지되었습니다"}
    
    auto_collector.stop_collector()
    return {"message": "자동 수집기가 중지되었습니다"}

@rest_router.get("/collector/symbols")
async def get_collector_symbols():
    """자동 수집기 모니터링 심볼 목록 조회"""
    from stock.backend.services.auto_collector import MOST_ACTIVE_STOCKS
    
    return {
        "total": len(MOST_ACTIVE_STOCKS),
        "symbols": MOST_ACTIVE_STOCKS
    }




