"""
AJEL Capital — Prices API Router
==================================
All external market data calls are proxied through here.
The browser NEVER calls Yahoo/CoinGecko/FMP directly — keys stay server-side.
"""
from fastapi import APIRouter, Query, Request, HTTPException
from typing import List, Optional
import logging

from data.market_data import MarketDataClient
from core.limiter import limiter

logger = logging.getLogger(__name__)
router = APIRouter()

# Singleton data client (reused across requests)
_data_client = MarketDataClient()


@router.get("/prices/{symbol}")
@limiter.limit("60/minute")
async def get_price(request: Request, symbol: str):
    """Get real-time price for a single symbol."""
    symbol = symbol.upper().strip()
    result = await _data_client.fetch_price(symbol)
    return result


@router.get("/prices")
@limiter.limit("30/minute")
async def get_prices_batch(request: Request, symbols: str = Query(..., description="Comma-separated symbols")):
    """
    Get real-time prices for multiple symbols at once.
    Example: /api/prices?symbols=AAPL,MSFT,TSLA
    """
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        raise HTTPException(status_code=400, detail="No symbols provided")
    if len(sym_list) > 50:
        raise HTTPException(status_code=400, detail="Max 50 symbols per request")

    results = await _data_client.fetch_prices_batch(sym_list)
    return {"prices": results, "count": len(results)}


@router.get("/historical/{symbol}")
@limiter.limit("30/minute")
async def get_historical(
    request: Request,
    symbol: str,
    period: str = Query("1y", description="1mo, 3mo, 6mo, 1y, 2y, 5y, max"),
    interval: str = Query("1wk", description="1d, 1wk, 1mo")
):
    """Get historical OHLCV candle data for charting."""
    symbol = symbol.upper().strip()
    result = await _data_client.fetch_historical(symbol, period=period, interval=interval)
    return result


@router.get("/fundamentals/{symbol}")
@limiter.limit("20/minute")
async def get_fundamentals(request: Request, symbol: str):
    """
    Get fundamental data for a symbol.
    Uses yfinance (free) + FMP enhancement if API key is set as env var.
    API key lives ONLY on the server — never exposed to the browser.
    """
    symbol = symbol.upper().strip()
    result = await _data_client.fetch_fundamental_data(symbol)
    return result


@router.get("/fear-greed")
@limiter.limit("20/minute")
async def get_fear_greed(request: Request):
    """Get current Fear & Greed indices (crypto + stock)."""
    result = await _data_client.fetch_fear_greed()
    return result
