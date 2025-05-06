from fastapi import APIRouter
import yfinance as yf

router = APIRouter()

@router.get("/stock/{ticker}")
def get_stock_data(ticker: str):
    stock = yf.Ticker(ticker)

    info = stock.get_info()
    chart = stock.history(period="1d", interval="1m").reset_index()

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
        "chartData": chart.tail(30).to_dict(orient="records")  
    }
