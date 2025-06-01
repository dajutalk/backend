from sqlalchemy import Column, Integer, String, Float, DateTime, Index, BigInteger, Boolean
from sqlalchemy.sql import func
from .connection import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

class User(Base):
    """사용자 모델"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    nickname = Column(String(100), nullable=False)
    password = Column(String(255), nullable=True)  # 카카오 로그인은 비밀번호 없음
    provider = Column(String(20), default="local")  # local, kakao 등
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def verify_password(self, password: str) -> bool:
        """비밀번호 검증"""
        if not self.password:
            return False
        return pwd_context.verify(password, self.password)
    
    def set_password(self, password: str):
        """비밀번호 해시화 후 저장"""
        self.password = pwd_context.hash(password)

class ChatMessage(Base):
    """채팅 메시지 모델 (사용자 연동)"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), nullable=False, index=True)
    user_id = Column(Integer, nullable=True)  # User.id 참조 (게스트는 NULL)
    nickname = Column(String(100), nullable=False)
    message = Column(String(1000), nullable=False)
    created_at = Column(DateTime, default=func.now(), index=True)
    
    __table_args__ = (
        Index('idx_symbol_created', 'symbol', 'created_at'),
        Index('idx_user_created', 'user_id', 'created_at'),
    )
