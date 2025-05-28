import asyncio
from fastapi import FastAPI
from stock.backend.api.stock_api import router as stock_router

# Create FastAPI app
app = FastAPI(
    title="Stock Market API",
    description="API for getting real-time and historical stock market data",
    version="1.0.0"
)

# Include routers
app.include_router(stock_router, prefix="/api/stock", tags=["Stocks"])

# Initialize event loop for WebSocket (if needed)
loop = asyncio.get_event_loop()

# Add startup and shutdown events if needed
@app.on_event("startup")
async def startup_event():
    # You can initialize the WebSocket client here if needed
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)




