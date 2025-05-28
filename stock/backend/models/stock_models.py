from typing import Optional, List
from pydantic import BaseModel

class StockQuote(BaseModel):
    c: float = None  # Current price
    h: float = None  # High price of the day
    l: float = None  # Low price of the day
    o: float = None  # Open price of the day
    pc: float = None  # Previous close price
    t: int = None    # Timestamp

class CompanyProfile(BaseModel):
    country: Optional[str] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None
    name: Optional[str] = None
    ticker: Optional[str] = None
    ipo: Optional[str] = None
    marketCapitalization: Optional[float] = None
    shareOutstanding: Optional[float] = None
    logo: Optional[str] = None
    weburl: Optional[str] = None
    finnhubIndustry: Optional[str] = None

class HistoricalData(BaseModel):
    c: List[float]  # Close prices
    h: List[float]  # High prices
    l: List[float]  # Low prices
    o: List[float]  # Open prices
    s: str         # Status
    t: List[int]   # Timestamps
    v: List[int]   # Volumes

class CombinedStockData(BaseModel):
    quote: Optional[StockQuote] = None
    profile: Optional[CompanyProfile] = None
