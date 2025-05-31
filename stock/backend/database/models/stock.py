from sqlalchemy import Column, Integer, String, Float, DateTime, Index
from sqlalchemy.sql import func
from ..connection import Base

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
