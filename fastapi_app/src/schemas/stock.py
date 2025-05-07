from pydantic import BaseModel
from typing import Optional, List, Dict

class StockSchema(BaseModel):
    ticker: str
    companyName: Optional[str]
    sector: Optional[str]
    isin: Optional[str]
    marketCap: Optional[float]
    priceNow: Optional[float]
    priceChangePercent: Optional[float]
    volume: Optional[int]
    per: Optional[float]
    dividendYield: Optional[float]
    chartData: Optional[List[Dict]] = []

    model_config = {
        "from_attributes": True
    }