"""
AJEL Capital — Intelligence API Router (Phase 2 + Phase 3)
============================================================
Composite scoring engine that evaluates:
  - Technical indicators (SMA, RSI, MACD via real yfinance data)
  - Fundamental health (P/E, debt/equity, revenue growth)
  - Macro environment (Fear & Greed, VIX-proxy)

Phase 3: Full AI-driven reports with actionable signals.
"""
from fastapi import APIRouter
from typing import Dict, Any
import logging

from data.market_data import MarketDataClient
from core.composite_scorer import CompositeScorer
from core.technical_analysis import TechnicalAnalyzer

logger = logging.getLogger(__name__)
router = APIRouter()

_data_client = MarketDataClient()
_scorer = CompositeScorer()
_tech = TechnicalAnalyzer()


@router.get("/score/{symbol}")
async def get_asset_score(symbol: str):
    """
    Full intelligence report for a single asset.
    Combines live prices, fundamentals, technicals, and macro into one composite score.
    """
    symbol = symbol.upper().strip()

    # 1. Fetch live price
    price_data = await _data_client.fetch_price(symbol)
    price = price_data.get("price", 0)

    # 2. Fetch historical for technicals
    hist = await _data_client.fetch_historical(symbol, period="1y", interval="1d")
    candles = hist.get("candles", [])

    # 3. Compute technical indicators from real data
    tech_indicators = _tech.compute_from_candles(candles)

    # 4. Fetch fundamentals
    fund_data = await _data_client.fetch_fundamental_data(symbol)

    # 5. Fetch macro sentiment
    fng = await _data_client.fetch_fear_greed()

    # 6. Build the score
    tech_input = {
        "price": price,
        "sma_50": tech_indicators.get("sma_50", 0),
        "sma_200": tech_indicators.get("sma_200", 0),
        "rsi": tech_indicators.get("rsi_14", 50),
    }
    fund_input = {
        "pe_ratio": fund_data.get("pe_ratio") or 20,
        "debt_equity": (fund_data.get("debt_to_equity") or 50) / 100,
        "rev_growth": fund_data.get("revenue_growth") or 0,
    }
    crypto_fng = fng.get("crypto", {})
    macro_input = {
        "fear_greed_idx": crypto_fng.get("value", 50) if crypto_fng else 50,
        "vix": tech_indicators.get("volatility", 18),
    }

    score = _scorer.compute_composite_score(tech_input, fund_input, macro_input)

    return {
        "ticker": symbol,
        "price": price,
        "technicals": tech_indicators,
        "fundamentals": {
            "pe_ratio": fund_data.get("pe_ratio"),
            "eps": fund_data.get("eps"),
            "revenue_growth": fund_data.get("revenue_growth"),
            "profit_margin": fund_data.get("profit_margin"),
            "debt_to_equity": fund_data.get("debt_to_equity"),
            "roe": fund_data.get("roe"),
            "beta": fund_data.get("beta"),
            "sector": fund_data.get("sector"),
            "name": fund_data.get("name", symbol),
        },
        "macro": {
            "fear_greed": fng,
        },
        "intelligence_report": score,
    }


@router.get("/scores")
async def get_batch_scores(symbols: str):
    """Get scores for multiple symbols (comma-separated)."""
    sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not sym_list:
        return {"error": "No symbols provided"}
    if len(sym_list) > 20:
        return {"error": "Max 20 symbols per batch score request"}

    results = {}
    for sym in sym_list:
        try:
            result = await get_asset_score(sym)
            results[sym] = {
                "composite": result["intelligence_report"]["composite"],
                "verdict": result["intelligence_report"]["verdict"],
                "price": result["price"],
                "breakdown": result["intelligence_report"]["breakdown"],
            }
        except Exception as e:
            logger.warning(f"Score computation failed for {sym}: {e}")
            results[sym] = {"error": str(e)}

    return {"scores": results}
