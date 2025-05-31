from fastapi import FastAPI, WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse
from stock.backend.api import stock, chat
from fastapi.middleware.cors import CORSMiddleware
from stock.backend.database import create_db_and_tables_safe
from stock.backend.services.auto_collector import auto_collector
from stock.backend.websocket_routes import router as websocket_router
from stock.backend.utils.logger import configure_logging
import logging

# 로깅 설정
configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Stock Backend API",
    version="1.0.0",
    description="주식 및 암호화폐 실시간 데이터 API"
)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영환경에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket 라우터 등록
app.include_router(stock.router)
app.include_router(chat.router)

# WebSocket 라우터 추가
app.include_router(websocket_router, tags=["websocket"])

# REST API 라우터 추가
app.include_router(stock.rest_router)

# 애플리케이션 시작 시 데이터베이스 테이블 생성
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info("🚀 Stock Backend API 시작...")
    
    # 데이터베이스 초기화 (실패해도 계속 진행)
    db_success = create_db_and_tables_safe()
    if db_success:
        logger.info("✅ 데이터베이스 초기화 완료")
    else:
        logger.warning("⚠️ 데이터베이스 초기화 실패 - 캐시 모드로 동작")
    
    # WebSocket 매니저 초기화
    from stock.backend.websocket_manager import manager
    logger.info("🔗 WebSocket 매니저 초기화 완료")
    
    # 잠시 대기 후 자동 수집기들 시작
    import asyncio
    await asyncio.sleep(2)
    
    # 암호화폐 자동 수집기 먼저 시작 (WebSocket 데이터 준비)
    try:
        from stock.backend.services.stock_service import start_crypto_collection
        start_crypto_collection()
        logger.info("₿ 암호화폐 데이터 자동 수집기 시작")
    except Exception as e:
        logger.error(f"❌ 암호화폐 수집기 시작 실패: {e}")
    
    # 추가 대기 후 주식 자동 수집기 시작
    await asyncio.sleep(1)
    try:
        auto_collector.start_collector()
        logger.info("🔄 주식 데이터 자동 수집기 시작")
    except Exception as e:
        logger.error(f"❌ 주식 수집기 시작 실패: {e}")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("🛑 Stock Backend API 종료...")
    
    # 모든 자동 수집기 중지
    try:
        auto_collector.stop_collector()
        logger.info("⏹️ 주식 데이터 자동 수집기 중지")
    except Exception as e:
        logger.error(f"❌ 주식 수집기 중지 실패: {e}")
    
    try:
        from stock.backend.services.stock_service import stop_crypto_collection
        stop_crypto_collection()
        logger.info("⏹️ 암호화폐 데이터 자동 수집기 중지")
    except Exception as e:
        logger.error(f"❌ 암호화폐 수집기 중지 실패: {e}")

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "message": "Stock Backend API is running",
        "version": "1.0.0"
    }



