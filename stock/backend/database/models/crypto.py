from sqlalchemy import Column, Integer, String, DateTime, Index, BigInteger
from sqlalchemy.sql import func
from ..connection import Base

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
