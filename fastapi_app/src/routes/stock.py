import time
from yfinance.exceptions import YFRateLimitError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..database.connection import get_db
from ..models.stock import Stock
from ..schemas.stock import StockSchema
import yfinance as yf

router = APIRouter(prefix="/stock", tags=["Stock"])


@router.get("/{ticker}", response_model=StockSchema)
async def get_stock_data(ticker: str, db: AsyncSession = Depends(get_db)):
    stock = yf.Ticker(ticker)
    retries = 3
    for attempt in range(retries):
        try:
            info = stock.get_info()
            break
        except YFRateLimitError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")
    
    chart = stock.history(period="1d", interval="1m").reset_index()
    chart_data = chart.tail(30)[["Datetime", "Close"]]
    chart_data = chart_data.rename(columns={"Datetime": "date", "Close": "close"}).to_dict(orient="records")

    return {
        "ticker": ticker,
        "companyName": info.get("longName"),
        "sector": info.get("sector"),
        "isin": stock.get_isin(),
        "marketCap": info.get("marketCap"),
        "priceNow": info.get("regularMarketPrice"),
        "priceChangePercent": info.get("regularMarketChangePercent"),
        "volume": info.get("volume"),
        "per": info.get("trailingPE"),
        "dividendYield": info.get("dividendYield"),
        "chartData": chart_data
    }