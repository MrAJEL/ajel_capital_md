"""
AJEL Capital — Technical Analysis Engine
==========================================
Computes real indicators from OHLCV candle data.
All calculations happen server-side using numpy.
"""
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """Calculates technical indicators from raw candle data."""

    def compute_from_candles(self, candles: List[Dict]) -> Dict[str, Any]:
        """
        Given a list of candles [{time, open, high, low, close, volume}, ...],
        compute all key technical indicators.
        """
        if not candles or len(candles) < 5:
            return {
                "sma_50": 0, "sma_200": 0, "ema_12": 0, "ema_26": 0,
                "rsi_14": 50, "macd": 0, "macd_signal": 0, "macd_histogram": 0,
                "atr_14": 0, "volatility": 18, "bb_upper": 0, "bb_lower": 0,
                "support": 0, "resistance": 0, "trend": "neutral",
                "error": "insufficient_data"
            }

        closes = np.array([c["close"] for c in candles], dtype=float)
        highs = np.array([c["high"] for c in candles], dtype=float)
        lows = np.array([c["low"] for c in candles], dtype=float)
        volumes = np.array([c.get("volume", 0) for c in candles], dtype=float)

        n = len(closes)
        current_price = closes[-1]

        # ── Simple Moving Averages ────────────────────────────────────────────
        sma_50 = float(np.mean(closes[-50:])) if n >= 50 else float(np.mean(closes))
        sma_200 = float(np.mean(closes[-200:])) if n >= 200 else float(np.mean(closes))
        sma_20 = float(np.mean(closes[-20:])) if n >= 20 else float(np.mean(closes))

        # ── Exponential Moving Averages ───────────────────────────────────────
        ema_12 = self._ema(closes, 12)
        ema_26 = self._ema(closes, 26)

        # ── MACD ──────────────────────────────────────────────────────────────
        macd_line = ema_12 - ema_26
        # Approximate signal line
        if n >= 26:
            macd_series = self._ema_series(closes, 12) - self._ema_series(closes, 26)
            if len(macd_series) >= 9:
                signal_line = float(self._ema_from_array(macd_series, 9))
            else:
                signal_line = macd_line
        else:
            signal_line = macd_line
        macd_histogram = macd_line - signal_line

        # ── RSI (14-period) ───────────────────────────────────────────────────
        rsi_14 = self._rsi(closes, 14)

        # ── ATR (14-period) ───────────────────────────────────────────────────
        atr_14 = self._atr(highs, lows, closes, 14)

        # ── Bollinger Bands (20-period, 2 std dev) ────────────────────────────
        if n >= 20:
            bb_std = float(np.std(closes[-20:]))
            bb_upper = sma_20 + 2 * bb_std
            bb_lower = sma_20 - 2 * bb_std
        else:
            bb_upper = current_price * 1.05
            bb_lower = current_price * 0.95

        # ── Volatility (annualized) ───────────────────────────────────────────
        if n >= 20:
            returns = np.diff(np.log(closes[-21:]))
            volatility = float(np.std(returns) * np.sqrt(252) * 100)
        else:
            volatility = 18.0

        # ── Support / Resistance (recent swing lows/highs) ────────────────────
        lookback = min(60, n)
        support = float(np.min(lows[-lookback:]))
        resistance = float(np.max(highs[-lookback:]))

        # ── Trend determination ───────────────────────────────────────────────
        if current_price > sma_50 > sma_200:
            trend = "bullish"
        elif current_price < sma_50 < sma_200:
            trend = "bearish"
        elif current_price > sma_50:
            trend = "mildly_bullish"
        elif current_price < sma_50:
            trend = "mildly_bearish"
        else:
            trend = "neutral"

        # ── Volume analysis ───────────────────────────────────────────────────
        avg_volume = float(np.mean(volumes[-20:])) if n >= 20 else float(np.mean(volumes))
        volume_ratio = float(volumes[-1] / avg_volume) if avg_volume > 0 else 1.0

        return {
            "sma_20": round(sma_20, 4),
            "sma_50": round(sma_50, 4),
            "sma_200": round(sma_200, 4),
            "ema_12": round(ema_12, 4),
            "ema_26": round(ema_26, 4),
            "rsi_14": round(rsi_14, 2),
            "macd": round(macd_line, 4),
            "macd_signal": round(signal_line, 4),
            "macd_histogram": round(macd_histogram, 4),
            "atr_14": round(atr_14, 4),
            "volatility": round(volatility, 2),
            "bb_upper": round(bb_upper, 4),
            "bb_lower": round(bb_lower, 4),
            "support": round(support, 4),
            "resistance": round(resistance, 4),
            "trend": trend,
            "volume_ratio": round(volume_ratio, 2),
            "current_price": round(current_price, 4),
        }

    # ── Helper methods ────────────────────────────────────────────────────────

    def _ema(self, data: np.ndarray, period: int) -> float:
        """Compute EMA, return the latest value."""
        if len(data) < period:
            return float(np.mean(data))
        multiplier = 2 / (period + 1)
        ema = float(np.mean(data[:period]))
        for price in data[period:]:
            ema = (float(price) - ema) * multiplier + ema
        return ema

    def _ema_series(self, data: np.ndarray, period: int) -> np.ndarray:
        """Compute full EMA series."""
        if len(data) < period:
            return data.copy()
        multiplier = 2 / (period + 1)
        result = np.zeros(len(data))
        result[period - 1] = np.mean(data[:period])
        for i in range(period, len(data)):
            result[i] = (data[i] - result[i - 1]) * multiplier + result[i - 1]
        return result[period - 1:]

    def _ema_from_array(self, data: np.ndarray, period: int) -> float:
        """Compute EMA of an already-computed array, return latest."""
        if len(data) < period:
            return float(np.mean(data))
        multiplier = 2 / (period + 1)
        ema = float(np.mean(data[:period]))
        for val in data[period:]:
            ema = (float(val) - ema) * multiplier + ema
        return ema

    def _rsi(self, closes: np.ndarray, period: int = 14) -> float:
        """Compute RSI."""
        if len(closes) < period + 1:
            return 50.0
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        avg_gain = float(np.mean(gains[:period]))
        avg_loss = float(np.mean(losses[:period]))

        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + float(gains[i])) / period
            avg_loss = (avg_loss * (period - 1) + float(losses[i])) / period

        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _atr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int = 14) -> float:
        """Compute Average True Range."""
        if len(closes) < 2:
            return 0.0
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(
                np.abs(highs[1:] - closes[:-1]),
                np.abs(lows[1:] - closes[:-1])
            )
        )
        if len(tr) < period:
            return float(np.mean(tr))
        return float(np.mean(tr[-period:]))
