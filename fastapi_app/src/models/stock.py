from sqlalchemy import Column, Integer, String, Float
from ..database.connection import Base

class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), nullable=False)
    companyName = Column(String(255))
    sector = Column(String(100))
    isin = Column(String(20))
    marketCap = Column(Float)
    priceNow = Column(Float)
    priceChangePercent = Column(Float)
    volume = Column(Integer)
    per = Column(Float)
    dividendYield = Column(Float)
