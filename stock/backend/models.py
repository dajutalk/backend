from sqlalchemy import Column, Integer, String, Float, DateTime, Index, BigInteger
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

class CryptoQuote(Base):
    """암호화폐 시세 데이터 모델"""
    __tablename__ = "crypto_quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), index=True, nullable=False)  # 암호화폐 심볼 (예: BTC, ETH)
    
    # 암호화폐 시세 데이터 (웹소켓 형식)
    s = Column(String(50), nullable=False)  # 전체 심볼 (BINANCE:BTCUSDT)
    p = Column(String(20), nullable=False)  # 현재 가격 (문자열)
    v = Column(String(20), nullable=True)   # 거래량 (문자열)
    t = Column(BigInteger, nullable=False)  # 타임스탬프 (밀리초) - INT에서 BigInteger로 변경
    
    # 메타 데이터
    created_at = Column(DateTime, default=datetime.utcnow)  # 데이터 생성 시간
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 마지막 업데이트 시간
    
    # 인덱스 설정
    __table_args__ = (
        Index("idx_crypto_symbol_created", "symbol", "created_at"),  # 심볼+시간 복합 인덱스
        Index("idx_crypto_created_at", "created_at"),                # 시간 단일 인덱스
        Index("idx_crypto_s", "s"),                                  # 전체 심볼 인덱스
        Index("idx_crypto_t", "t"),                                  # 타임스탬프 인덱스 추가
    )


