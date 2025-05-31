from fastapi import FastAPI, WebSocket,WebSocketDisconnect
from fastapi.responses import FileResponse
from stock.backend.api import stock, chat
from fastapi.middleware.cors import CORSMiddleware
from stock.backend.database import create_db_and_tables
from stock.backend.services.auto_collector import auto_collector

app = FastAPI()

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

# REST API 라우터 추가
app.include_router(stock.rest_router)

# 애플리케이션 시작 시 데이터베이스 테이블 생성
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    print("🚀 Stock Backend API 시작...")
    create_db_and_tables()
    print("✅ 데이터베이스 초기화 완료")
    
    # 잠시 대기 후 자동 수집기 시작 (서버가 완전히 시작된 후)
    import asyncio
    await asyncio.sleep(3)
    auto_collector.start_collector()
    print("🔄 주식 데이터 자동 수집기 시작")

@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    print("🛑 Stock Backend API 종료...")
    
    # 자동 수집기 중지
    auto_collector.stop_collector()
    print("⏹️ 주식 데이터 자동 수집기 중지")



