from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class StockQuote(Base):
    """주식 시세 데이터 모델"""
    __tablename__ = "stock_quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)  # 주식 심볼 (예: AAPL)
    
    # 주식 시세 데이터
    c = Column(Float, nullable=False)  # Current price (현재 가격)
    d = Column(Float, nullable=True)   # Change (변동폭)
    dp = Column(Float, nullable=True)  # Percent change (변동률 %)
    h = Column(Float, nullable=True)   # High price of the day (고가)
    l = Column(Float, nullable=True)   # Low price of the day (저가)
    o = Column(Float, nullable=True)   # Open price of the day (시가)
    pc = Column(Float, nullable=True)  # Previous close price (전일 종가)
    
    # 메타 데이터
    created_at = Column(DateTime, default=datetime.utcnow)  # 데이터 생성 시간
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 마지막 업데이트 시간
    
    # 인덱스 설정
    __table_args__ = (
        Index("idx_symbol_created", "symbol", "created_at"),  # 심볼+시간 복합 인덱스
        Index("idx_created_at", "created_at"),                # 시간 단일 인덱스
    )

# 📈 주요 특징:
# 1. Primary Key: id (자동 증가)
# 2. Stock Symbol: symbol (AAPL, MSFT 등 최대 20자)
# 3. Price Data: Finnhub API 표준 필드들
#    - c: Current price (현재가)
#    - d: Change (변동폭)  
#    - dp: Percent change (변동률 %)
#    - h: High price (고가)
#    - l: Low price (저가)
#    - o: Open price (시가)
#    - pc: Previous close (전일 종가)
# 4. Timestamps: 생성/수정 시간 자동 관리
# 5. Indexes: 빠른 조회를 위한 인덱스 설정

# 🔄 1분 자동 수집 시스템 설명:
# 
# 📊 수집 대상: 50개 주요 주식 (MOST_ACTIVE_STOCKS)
# ⏰ 수집 주기: 1분마다 반복 실행
# 🎯 수집 방식: 자체 REST API 호출 → DB 저장
# 🚀 처리 방식: 비동기 병렬 처리 (동시에 50개 요청)
# 
# 💾 저장 구조:
# - 매분마다 50개 레코드 생성 (각 심볼당 1개)
# - 시간순 정렬을 위한 created_at 자동 기록
# - 중복 데이터도 허용 (시계열 데이터 특성상)
