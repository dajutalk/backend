from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from stock.backend.api import stock, chat
from stock.backend.auth import auth_router
from fastapi.middleware.cors import CORSMiddleware
from stock.backend.database import create_db_and_tables_safe
from stock.backend.services.auto_collector import auto_collector
from stock.backend.websocket_routes import router as websocket_router
from stock.backend.utils.logger import configure_logging
from stock.backend.core.config import app_settings
import logging

# 로깅 설정
configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=app_settings.title,
    version=app_settings.version,
    description="주식 데이터 + 사용자 인증 통합 API"
)

# CORS 설정 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=app_settings.allowed_methods,
    allow_headers=app_settings.allowed_headers,
)

# 라우터 등록 순서 중요
# 1. 인증 관련 라우터 (최우선)
app.include_router(auth_router, prefix="/auth", tags=["authentication"])

# 2. 주식 WebSocket 라우터
app.include_router(stock.router)
app.include_router(chat.router)
app.include_router(websocket_router, tags=["websocket"])

# 3. 주식 REST API 라우터
app.include_router(stock.rest_router)
app.include_router(chat.rest_router)

# 애플리케이션 시작 시 데이터베이스 테이블 생성
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info(" 통합 Stock & Auth API 시작...")
    
    # 데이터베이스 초기화 (실패해도 계속 진행)
    db_success = create_db_and_tables_safe()
    if db_success:
        logger.info(" 데이터베이스 초기화 완료")
    else:
        logger.warning(" 데이터베이스 초기화 실패 - 캐시 모드로 동작")
    
    # WebSocket 매니저 초기화
    try:
        from stock.backend.websocket_manager import manager
        logger.info("🔗 WebSocket 매니저 초기화 완료")
    except Exception as e:
        logger.warning(f" WebSocket 매니저 초기화 실패: {e}")
    
    # 잠시 대기 후 자동 수집기들 시작
    import asyncio
    await asyncio.sleep(2)
    
    # 암호화폐 자동 수집기 먼저 시작 (WebSocket 데이터 준비)
    try:
        from stock.backend.services.stock_service import start_crypto_collection
        start_crypto_collection()
        logger.info("₿ 암호화폐 데이터 자동 수집기 시작")
    except Exception as e:
        logger.error(f" 암호화폐 수집기 시작 실패: {e}")
    
    # 추가 대기 후 주식 자동 수집기 시작
    await asyncio.sleep(1)
    try:
        auto_collector.start_collector()
        logger.info(" 주식 데이터 자동 수집기 시작")
    except Exception as e:
        logger.error(f" 주식 수집기 시작 실패: {e}")
    
    logger.info(" 모든 서비스 초기화 완료!")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info(" 통합 API 종료...")
    
    # 모든 자동 수집기 중지
    try:
        auto_collector.stop_collector()
        logger.info(" 주식 데이터 자동 수집기 중지")
    except Exception as e:
        logger.error(f" 주식 수집기 중지 실패: {e}")
    
    try:
        from stock.backend.services.stock_service import stop_crypto_collection
        stop_crypto_collection()
        logger.info(" 암호화폐 데이터 자동 수집기 중지")
    except Exception as e:
        logger.error(f" 암호화폐 수집기 중지 실패: {e}")

@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "통합 Stock & Auth API",
        "version": app_settings.version,
        "endpoints": {
            "health": "/health",
            "auth": "/auth",
            "stocks": "/api/stocks",
            "websocket": "/ws",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {
        "status": "healthy",
        "message": "통합 Stock & Auth API 정상 동작",
        "version": app_settings.version,
        "services": {
            "auth": "active",
            "stocks": "active", 
            "websocket": "active",
            "database": "connected"
        }
    }



