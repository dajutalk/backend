from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from stock.backend.database.connection import Base

class TransactionHistory(Base):
    """모의투자 거래 기록"""
    __tablename__ = "transaction_histories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    trade_type = Column(String(10), nullable=False)  # 예: 'BUY' 또는 'SELL'
    symbol = Column(String(20), nullable=False)      # 어떤 종목을 거래했는지
    quantity = Column(Integer, nullable=False)       # 거래 수량
    total_price = Column(BigInteger, nullable=False) # 거래 총액
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=func.now(), index=True)

    user = relationship("User", backref="transaction_histories")

    def __repr__(self):
        return f"<TransactionHistory(id={self.id}, user_id={self.user_id}, type='{self.trade_type}', symbol='{self.symbol}', quantity={self.quantity}, total={self.total_price})>"

class MockBalance(Base):
    """유저별 모의투자 잔고"""
    __tablename__ = "mock_balances"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    balance = Column(BigInteger, nullable=False, default=10_000)

    user = relationship("User", backref="mock_balance")

    def __repr__(self):
        return f"<MockBalance(user_id={self.user_id}, balance={self.balance})>"