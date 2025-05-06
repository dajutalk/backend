from pydantic import BaseModel, ConfigDict
from beanie import Document


class Stock(BaseModel):
    ticker: str
    companyName: str
    sector:  str
    isin:  str
    marketCap:  str
    priceNow: str
    priceChangePercent: str
    volume: str
    per:str
    dividendYield:str
    chartData:list[dict]

    class Config:
        json_schema_extra = {
            "example": {
                "ticker": "AAPL",
                "companyName": "Apple Inc.",
                "sector": "Technology",
                "isin": "US0378331005",
                "marketCap": 2500000000000,
                "priceNow": 150.00,
                "priceChangePercent": 1.5,
                "volume": 1000000,
                "per": 28.5,
                "dividendYield": 0.005,
                "chartData": [
                    {"date": "2023-01-01", "close": 145.00},
                    {"date": "2023-01-02", "close": 146.00},
                    # Add more data points as needed
                ]
            }
        }