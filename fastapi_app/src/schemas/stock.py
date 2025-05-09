from pydantic import BaseModel
from typing import Optional

class StockSchema(BaseModel):
    ticker: str
    sector: Optional[str]
    isin: Optional[str]
    marketCap: Optional[float]
    priceNow: Optional[float]
    priceChangePercent: Optional[float]
    volume: Optional[int]
    per: Optional[float]
    dividendYield: Optional[float]
    

    model_config = {
        "from_attributes": True
    }