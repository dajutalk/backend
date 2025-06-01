from sqlalchemy import Column, Integer, String, Float, DateTime, Index, BigInteger
from sqlalchemy.sql import func
from .connection import Base

class StockQuote(Base):
    """주식 시세 모델"""
    __tablename__ = "stock_quotes"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    c = Column(Float, nullable=False)  # 현재가
    d = Column(Float, nullable=True)   # 변동폭
    dp = Column(Float, nullable=True)  # 변동률
    h = Column(Float, nullable=True)   # 고가
    l = Column(Float, nullable=True)   # 저가
    o = Column(Float, nullable=True)   # 시가
    pc = Column(Float, nullable=True)  # 전일종가
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 복합 인덱스
    __table_args__ = (
        Index('idx_symbol_created', 'symbol', 'created_at'),
    )

    def __repr__(self):
        return f"<StockQuote(symbol='{self.symbol}', price={self.c}, time='{self.created_at}')>"

class CryptoQuote(Base):
    """암호화폐 시세 모델"""
    __tablename__ = "crypto_quotes"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)  # BTC, ETH 등
    s = Column(String(50), nullable=False)  # BINANCE:BTCUSDT
    p = Column(String(20), nullable=False)  # 가격 (문자열)
    v = Column(String(20), nullable=True)   # 거래량 (문자열)
    t = Column(BigInteger, nullable=False)  # 타임스탬프 (밀리초)
    created_at = Column(DateTime, default=func.now(), index=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # 복합 인덱스
    __table_args__ = (
        Index('idx_symbol_created', 'symbol', 'created_at'),
        Index('idx_timestamp', 't'),
    )

    def __repr__(self):
        return f"<CryptoQuote(symbol='{self.symbol}', price={self.p}, time='{self.created_at}')>"

class ChatMessage(Base):
    """채팅 메시지 모델"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)  # 주식/암호화폐 심볼
    user_id = Column(String(50), nullable=False)  # 사용자 ID
    nickname = Column(String(100), nullable=False)  # 닉네임
    message = Column(String(1000), nullable=False)  # 메시지 내용
    created_at = Column(DateTime, default=func.now(), index=True)
    
    # 인덱스 설정
    __table_args__ = (
        Index('idx_symbol_created', 'symbol', 'created_at'),
        Index('idx_user_created', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ChatMessage(symbol='{self.symbol}', user='{self.nickname}', time='{self.created_at}')>"
