from fastapi import APIRouter, Path, Query, HTTPException
from typing import Optional
from stock.backend.models.stock_models import StockQuote, CompanyProfile, HistoricalData, CombinedStockData
from stock.backend.services.stock_service import get_stock_quote, get_company_profile, get_historical_data, get_stock_data_async

router = APIRouter()

@router.get("/quote/{symbol}", response_model=StockQuote, tags=["Stocks"])
def get_stock_quote_endpoint(symbol: str = Path(..., description="Stock symbol (e.g., AAPL)")):
    """
    Get real-time stock quote information for a specific symbol.
    
    Returns current price, daily high/low prices, open price, and previous close price.
    """
    result = get_stock_quote(symbol)
    if not result:
        raise HTTPException(status_code=404, detail=f"Data not found for symbol {symbol}")
    return result

@router.get("/company/profile/{symbol}", response_model=CompanyProfile, tags=["Companies"])
def get_company_profile_endpoint(symbol: str = Path(..., description="Stock symbol (e.g., AAPL)")):
    """
    Get detailed company information for a specific stock symbol.
    
    Returns company details including name, country, industry, website and logo.
    """
    result = get_company_profile(symbol)
    if not result:
        raise HTTPException(status_code=404, detail=f"Company profile not found for symbol {symbol}")
    return result

@router.get("/historical/{symbol}", response_model=HistoricalData, tags=["Stocks"])
def get_historical_data_endpoint(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)"),
    from_date: Optional[int] = Query(None, description="Start timestamp (Unix time)"),
    to_date: Optional[int] = Query(None, description="End timestamp (Unix time)"),
    resolution: str = Query("D", description="Data resolution: 1, 5, 15, 30, 60, D, W, M (minutes or day/week/month)")
):
    """
    Get historical stock price data for a specific symbol.
    
    Returns candle data (open, high, low, close) with timestamps.
    """
    result = get_historical_data(symbol, from_date, to_date, resolution)
    if not result or result.get("s") == "no_data":
        raise HTTPException(status_code=404, detail=f"Historical data not found for symbol {symbol}")
    return result

@router.get("/combined/{symbol}", response_model=CombinedStockData, tags=["Stocks"])
async def get_combined_stock_data_endpoint(symbol: str = Path(..., description="Stock symbol (e.g., AAPL)")):
    """
    Get combined stock data including real-time quotes and company profile.
    
    Returns a combined object with quote and profile information.
    """
    result = await get_stock_data_async(symbol)
    if not result["quote"] and not result["profile"]:
        raise HTTPException(status_code=404, detail=f"Data not found for symbol {symbol}")
    return result
