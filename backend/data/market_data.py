"""
AJEL Capital — Market Data Client (Phase 2 — Docker-safe)
============================================================
Security principles:
  - All API keys are read from environment variables (never hard-coded)
  - All external HTTP calls happen server-side (browser never sees API keys)
  - Results are cached in Redis to minimize external API calls

Data sources (all free, no API key required):
  - Yahoo Finance v8 HTTP API  — stocks, ETFs (direct HTTPS, no library)
  - CoinGecko                  — crypto prices
  - FMP (optional, env key)    — enhanced fundamentals
"""
import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

import httpx

from data.cache import cache_get, cache_set

logger = logging.getLogger(__name__)

# ── Crypto symbols that need CoinGecko instead of Yahoo ──────────────────────
COINGECKO_IDS = {
    'BTC-USD': 'bitcoin', 'ETH-USD': 'ethereum', 'SOL-USD': 'solana',
    'BNB-USD': 'binancecoin', 'ADA-USD': 'cardano', 'XRP-USD': 'ripple',
    'DOGE-USD': 'dogecoin', 'DOT-USD': 'polkadot',
}

# Cache TTLs (seconds)
PRICE_CACHE_TTL    = 60       # 1 minute for live prices
HIST_CACHE_TTL     = 3600     # 1 hour for historical data
FUND_CACHE_TTL     = 86400    # 24 hours for fundamentals

# Headers to avoid Yahoo blocking
YAHOO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json",
}

# Period mapping for Yahoo chart API
PERIOD_MAP = {
    "1mo": ("1mo", "1d"),
    "3mo": ("3mo", "1d"),
    "6mo": ("6mo", "1d"),
    "1y": ("1y", "1wk"),
    "2y": ("2y", "1wk"),
    "5y": ("5y", "1mo"),
    "max": ("max", "1mo"),
}


class MarketDataClient:
    """
    Core data digester — server-side only.
    Fetches real market data via direct HTTP (no yfinance library).
    """

    def __init__(self):
        self.fmp_api_key = os.getenv("FMP_API_KEY")
        if not self.fmp_api_key:
            logger.warning("FMP_API_KEY not set — fundamentals via FMP disabled, using Yahoo fallback.")

    # ── Live Price ────────────────────────────────────────────────────────────
    async def fetch_price(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch real-time price for any symbol (stocks, ETFs, crypto).
        Uses Yahoo Finance v8 quote API directly (no library).
        Falls back to CoinGecko for crypto tickers.
        """
        cache_key = f"price:{symbol}"
        cached = cache_get(cache_key)
        if cached:
            return {**cached, "cached": True}

        result = await self._fetch_yahoo_quote(symbol)
        if not result and symbol in COINGECKO_IDS:
            result = await self._fetch_price_coingecko(symbol)

        if result:
            cache_set(cache_key, result, PRICE_CACHE_TTL)

        return result or {"symbol": symbol, "error": "price_unavailable", "price": 0}

    async def fetch_prices_batch(self, symbols: List[str]) -> Dict[str, Any]:
        """Fetch prices for multiple symbols efficiently via Yahoo batch quote."""
        results = {}
        uncached = []

        for sym in symbols:
            cached = cache_get(f"price:{sym}")
            if cached:
                results[sym] = {**cached, "cached": True}
            else:
                uncached.append(sym)

        if not uncached:
            return results

        # Split into Yahoo-compatible and crypto
        yahoo_syms = [s for s in uncached if s not in COINGECKO_IDS]
        crypto_syms = [s for s in uncached if s in COINGECKO_IDS]

        # Batch fetch from Yahoo (supports comma-separated)
        if yahoo_syms:
            yahoo_results = await self._fetch_yahoo_quotes_batch(yahoo_syms)
            for sym, rec in yahoo_results.items():
                results[sym] = rec
                cache_set(f"price:{sym}", rec, PRICE_CACHE_TTL)

        # Fetch crypto from CoinGecko
        for sym in crypto_syms:
            rec = await self._fetch_price_coingecko(sym)
            if rec:
                results[sym] = rec
                cache_set(f"price:{sym}", rec, PRICE_CACHE_TTL)

        return results

    async def _fetch_yahoo_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch a single quote from Yahoo Finance v8 API (direct HTTP)."""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {"range": "2d", "interval": "1d", "includePrePost": "false"}
            async with httpx.AsyncClient(timeout=12.0, headers=YAHOO_HEADERS, follow_redirects=True) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            chart = data.get("chart", {}).get("result", [])
            if not chart:
                return None

            meta = chart[0].get("meta", {})
            closes = chart[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])
            # Filter None values
            closes = [c for c in closes if c is not None]

            if not closes:
                return None

            price = closes[-1]
            prev = closes[-2] if len(closes) >= 2 else meta.get("chartPreviousClose", price)
            if prev is None or prev == 0:
                prev = price

            change = price - prev
            change_pct = (change / prev * 100) if prev else 0

            return {
                "symbol": symbol,
                "price": round(float(price), 4),
                "change": round(float(change), 4),
                "changePct": round(float(change_pct), 4),
                "prevClose": round(float(prev), 4),
                "high52": meta.get("fiftyTwoWeekHigh"),
                "low52": meta.get("fiftyTwoWeekLow"),
                "volume": meta.get("regularMarketVolume"),
                "marketCap": None,
                "source": "yahoo_v8"
            }
        except Exception as e:
            logger.warning(f"Yahoo v8 quote failed for {symbol}: {e}")
            return None

    async def _fetch_yahoo_quotes_batch(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch multiple quotes from Yahoo explicitly using true batch API to avoid silent rate-limiting."""
        results = {}
        if not symbols:
            return results
        
        try:
            sym_str = ",".join(symbols)
            url = f"https://query1.finance.yahoo.com/v7/finance/quote?symbols={sym_str}"
            async with httpx.AsyncClient(timeout=15.0, headers=YAHOO_HEADERS, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
            
            quotes = data.get("quoteResponse", {}).get("result", [])
            for q in quotes:
                sym = q.get("symbol")
                price = q.get("regularMarketPrice")
                if not sym or price is None:
                    continue
                results[sym] = {
                    "symbol": sym,
                    "price": round(float(price), 4),
                    "change": round(float(q.get("regularMarketChange", 0)), 4),
                    "changePct": round(float(q.get("regularMarketChangePercent", 0)), 4),
                    "prevClose": round(float(q.get("regularMarketPreviousClose", price)), 4),
                    "high52": q.get("fiftyTwoWeekHigh"),
                    "low52": q.get("fiftyTwoWeekLow"),
                    "volume": q.get("regularMarketVolume"),
                    "marketCap": q.get("marketCap"),
                    "source": "yahoo_v7_batch"
                }
        except Exception as e:
            logger.warning(f"Yahoo v7 batch quote failed: {e}. Falling back to sequential.")
            async def fetch_one(sym: str):
                rec = await self._fetch_yahoo_quote(sym)
                if rec:
                    results[sym] = rec

            semaphore = asyncio.Semaphore(5)
            async def limited_fetch(sym: str):
                async with semaphore:
                    await fetch_one(sym)

            tasks = [limited_fetch(sym) for sym in symbols]
            await asyncio.gather(*tasks, return_exceptions=True)

        return results

    async def _fetch_price_coingecko(self, symbol: str) -> Optional[Dict[str, Any]]:
        cg_id = COINGECKO_IDS.get(symbol)
        if not cg_id:
            return None
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd&include_24hr_change=true"
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                entry = data.get(cg_id, {})
                price = entry.get("usd", 0)
                change_pct = entry.get("usd_24h_change", 0)
                change = price * change_pct / 100
                return {
                    "symbol": symbol,
                    "price": round(price, 4),
                    "change": round(change, 4),
                    "changePct": round(change_pct, 4),
                    "prevClose": round(price - change, 4),
                    "source": "CoinGecko"
                }
        except Exception as e:
            logger.warning(f"CoinGecko fetch failed for {symbol}: {e}")
            return None

    # ── Historical Data ───────────────────────────────────────────────────────
    async def fetch_historical(self, symbol: str, period: str = "1y", interval: str = "1wk") -> Dict[str, Any]:
        """Fetch OHLCV historical data from Yahoo v8 chart API. Cached in Redis."""
        cache_key = f"hist:{symbol}:{period}:{interval}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        try:
            result = await self._fetch_yahoo_chart(symbol, period, interval)
            if result and result.get("candles"):
                cache_set(cache_key, result, HIST_CACHE_TTL)
            return result or {"symbol": symbol, "candles": [], "error": "no_data"}
        except Exception as e:
            logger.error(f"Historical fetch failed for {symbol}: {e}")
            return {"symbol": symbol, "candles": [], "error": str(e)}

    async def _fetch_yahoo_chart(self, symbol: str, period: str, interval: str) -> Optional[Dict[str, Any]]:
        """Fetch OHLCV candle data from Yahoo Finance v8 chart API."""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            params = {"range": period, "interval": interval, "includePrePost": "false"}
            async with httpx.AsyncClient(timeout=15.0, headers=YAHOO_HEADERS, follow_redirects=True) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            chart = data.get("chart", {}).get("result", [])
            if not chart:
                return None

            timestamps = chart[0].get("timestamp", [])
            quote = chart[0].get("indicators", {}).get("quote", [{}])[0]
            opens = quote.get("open", [])
            highs = quote.get("high", [])
            lows = quote.get("low", [])
            closes = quote.get("close", [])
            volumes = quote.get("volume", [])

            candles = []
            for i, ts in enumerate(timestamps):
                o = opens[i] if i < len(opens) and opens[i] is not None else 0
                h = highs[i] if i < len(highs) and highs[i] is not None else 0
                l = lows[i] if i < len(lows) and lows[i] is not None else 0
                c = closes[i] if i < len(closes) and closes[i] is not None else 0
                v = volumes[i] if i < len(volumes) and volumes[i] is not None else 0

                if c > 0:
                    candles.append({
                        "time": int(ts),
                        "open": round(float(o), 4),
                        "high": round(float(h), 4),
                        "low": round(float(l), 4),
                        "close": round(float(c), 4),
                        "volume": int(v)
                    })

            return {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "candles": candles,
                "count": len(candles)
            }
        except Exception as e:
            logger.warning(f"Yahoo chart fetch failed for {symbol}: {e}")
            return None

    # ── Fundamentals ──────────────────────────────────────────────────────────
    async def fetch_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch fundamentals from Yahoo Finance quoteSummary API (free, no key).
        Optionally enhanced with FMP if API key is provided.
        """
        cache_key = f"fund:{symbol}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        result = await self._fetch_yahoo_fundamentals(symbol)

        if self.fmp_api_key and result:
            fmp_data = await self._fetch_fundamentals_fmp(symbol)
            if fmp_data:
                result.update(fmp_data)

        if result:
            cache_set(cache_key, result, FUND_CACHE_TTL)

        return result or {"symbol": symbol, "error": "fundamentals_unavailable"}

    async def _fetch_yahoo_fundamentals(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch fundamentals from Yahoo Finance v10 quoteSummary (direct HTTP)."""
        try:
            modules = "defaultKeyStatistics,financialData,summaryProfile,summaryDetail,earnings"
            url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
            params = {"modules": modules}
            async with httpx.AsyncClient(timeout=12.0, headers=YAHOO_HEADERS, follow_redirects=True) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()

            result_data = data.get("quoteSummary", {}).get("result", [])
            if not result_data:
                return None

            modules_data = result_data[0]
            stats = modules_data.get("defaultKeyStatistics", {})
            fin = modules_data.get("financialData", {})
            profile = modules_data.get("summaryProfile", {})
            detail = modules_data.get("summaryDetail", {})

            def _raw(obj, key, default=None):
                """Extract raw value from Yahoo's {raw: ..., fmt: ...} structure."""
                val = obj.get(key, {})
                if isinstance(val, dict):
                    return val.get("raw", default)
                return val if val else default

            return {
                "symbol": symbol,
                "name": symbol,
                "sector": profile.get("sector"),
                "industry": profile.get("industry"),
                "pe_ratio": _raw(detail, "trailingPE") or _raw(stats, "forwardPE"),
                "eps": _raw(stats, "trailingEps") or _raw(detail, "trailingEps"),
                "peg_ratio": _raw(stats, "pegRatio"),
                "price_to_book": _raw(stats, "priceToBook"),
                "debt_to_equity": _raw(fin, "debtToEquity"),
                "revenue": _raw(fin, "totalRevenue"),
                "net_income": _raw(fin, "netIncomeToCommon") if "netIncomeToCommon" in fin else None,
                "profit_margin": _raw(fin, "profitMargins"),
                "revenue_growth": _raw(fin, "revenueGrowth"),
                "roe": _raw(fin, "returnOnEquity"),
                "roa": _raw(fin, "returnOnAssets"),
                "beta": _raw(stats, "beta"),
                "dividend_yield": _raw(detail, "dividendYield"),
                "shares_outstanding": _raw(stats, "sharesOutstanding"),
                "equity": None,
                "total_debt": _raw(fin, "totalDebt"),
                "market_cap": _raw(detail, "marketCap"),
                "source": "yahoo_v10"
            }
        except Exception as e:
            logger.warning(f"Yahoo fundamentals fetch failed for {symbol}: {e}")
            return None

    async def _fetch_fundamentals_fmp(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Enhanced fundamentals from FMP (uses server-side API key from env var)."""
        if not self.fmp_api_key:
            return None
        try:
            url = f"https://financialmodelingprep.com/api/v3/profile/{symbol}?apikey={self.fmp_api_key}"
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
                if not data:
                    return None
                d = data[0]
                return {
                    "description": d.get("description"),
                    "website": d.get("website"),
                    "exchange": d.get("exchangeShortName"),
                    "country": d.get("country"),
                    "fmp_enhanced": True
                }
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning(f"FMP Rate limit exceeded for {symbol}.")
            else:
                # Never log the URL — it contains the API key
                logger.warning(f"FMP fetch failed for {symbol}: HTTP {e.response.status_code}")
            return None
        except Exception as e:
            # Never log the URL — it contains the API key
            logger.warning(f"FMP fetch error for {symbol}: {type(e).__name__}")
            return None

    # ── Fear & Greed ──────────────────────────────────────────────────────────
    async def fetch_fear_greed(self) -> Dict[str, Any]:
        """Fetch crypto and stock Fear & Greed indices."""
        cache_key = "fear_greed"
        cached = cache_get(cache_key)
        if cached:
            return cached

        result = {"crypto": None, "stock": None}

        # Crypto from alternative.me (free, no key)
        try:
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                resp = await client.get("https://api.alternative.me/fng/")
                resp.raise_for_status()
                data = resp.json()
                if data and data.get("data") and data["data"][0]:
                    entry = data["data"][0]
                    result["crypto"] = {
                        "value": int(entry["value"]),
                        "label": entry["value_classification"]
                    }
        except Exception as e:
            logger.warning(f"Crypto F&G fetch failed: {e}")

        if result:
            cache_set(cache_key, result, 300)  # 5 min cache

        return result
