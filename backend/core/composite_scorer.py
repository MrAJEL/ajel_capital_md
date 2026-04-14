"""
AJEL Capital — Composite Scorer (Phase 2.3 + Phase 3)
=====================================================
Evaluates assets across 3 pillars: Technical, Fundamental, Macro.
Produces a 0-100 composite score with a human-readable verdict.

Phase 3 addition: actionable signals with conviction levels.
"""


class CompositeScorer:
    """
    Multi-pillar scoring engine.
    Weights: Technical 40, Fundamental 35, Macro 25.
    """

    def __init__(self):
        self.weights = {
            "technical": 40,
            "fundamental": 35,
            "macro": 25,
        }

    def evaluate_technical(self, price: float, sma_50: float, sma_200: float, rsi: float) -> int:
        """Score technical setup (0-40)."""
        score = 0

        # Trend alignment
        if price > sma_50 > sma_200:
            score += 15  # Golden cross territory
        elif price > sma_50:
            score += 10  # Above short-term trend
        elif price > sma_200:
            score += 5   # Above long-term but below short-term

        # RSI zones
        if 30 < rsi < 70:
            score += 10  # Healthy range
        elif rsi <= 30:
            score += 15  # Oversold = opportunity
        elif rsi >= 70:
            score += 3   # Overbought = caution but not 0

        # Price vs SMA distance (momentum)
        if sma_50 > 0:
            momentum_pct = ((price - sma_50) / sma_50) * 100
            if 0 < momentum_pct < 10:
                score += 10  # Healthy uptrend
            elif -5 < momentum_pct <= 0:
                score += 7   # Mild pullback
            elif momentum_pct >= 10:
                score += 5   # Extended but still up

        return min(score, self.weights["technical"])

    def evaluate_fundamental(self, pe_ratio: float, debt_equity: float, rev_growth: float) -> int:
        """Score fundamental health (0-35)."""
        score = 0

        # P/E ratio assessment
        if pe_ratio is not None and pe_ratio > 0:
            if pe_ratio < 15:
                score += 15  # Value territory
            elif pe_ratio < 25:
                score += 10  # Reasonable
            elif pe_ratio < 40:
                score += 5   # Growth premium
            # pe > 40: no points (expensive)

        # Debt-to-equity
        if debt_equity is not None:
            if debt_equity < 0.5:
                score += 10  # Strong balance sheet
            elif debt_equity < 1.0:
                score += 7   # Manageable
            elif debt_equity < 2.0:
                score += 3   # Leveraged

        # Revenue growth
        if rev_growth is not None:
            if rev_growth > 0.20:
                score += 10  # Hyper-growth
            elif rev_growth > 0.10:
                score += 8   # Strong growth
            elif rev_growth > 0.05:
                score += 5   # Moderate growth
            elif rev_growth > 0:
                score += 3   # Positive but slow

        return min(score, self.weights["fundamental"])

    def evaluate_macro(self, fear_greed_idx: int, vix: float) -> int:
        """Score macro environment (0-25)."""
        score = 0

        # Fear & Greed — contrarian logic
        if fear_greed_idx < 25:
            score += 15  # Extreme fear = max opportunity
        elif fear_greed_idx < 40:
            score += 12  # Fear = opportunity
        elif fear_greed_idx < 60:
            score += 8   # Neutral
        elif fear_greed_idx < 75:
            score += 5   # Greed = caution
        else:
            score += 2   # Extreme greed = very cautious

        # Volatility as a proxy for VIX
        if vix is not None:
            if vix < 15:
                score += 8   # Low vol, calm market
            elif vix < 25:
                score += 6   # Normal
            elif vix < 35:
                score += 4   # Elevated but tradeable
            else:
                score += 10  # Extreme vol = mean-reversion opportunity

        return min(score, self.weights["macro"])

    def compute_composite_score(self, tech_data: dict, fund_data: dict, macro_data: dict) -> dict:
        """
        Compute the full composite score with verdict.
        Returns { composite, breakdown, verdict, conviction, action }
        """
        t_score = self.evaluate_technical(**tech_data)
        f_score = self.evaluate_fundamental(**fund_data)
        m_score = self.evaluate_macro(**macro_data)

        total = t_score + f_score + m_score

        # Verdict mapping
        if total >= 80:
            verdict = "STRONG BUY"
            conviction = "high"
            action = "Accumulate aggressively. All pillars align."
        elif total >= 65:
            verdict = "BUY"
            conviction = "medium-high"
            action = "Good entry. Build position with scaling."
        elif total >= 50:
            verdict = "HOLD"
            conviction = "neutral"
            action = "Maintain position. Wait for clearer signals."
        elif total >= 35:
            verdict = "CAUTION"
            conviction = "low"
            action = "Reduce exposure. Tighten stop-losses."
        elif total >= 20:
            verdict = "SELL"
            conviction = "medium"
            action = "Exit position. Multiple pillars weakening."
        else:
            verdict = "STRONG SELL"
            conviction = "high"
            action = "Exit immediately. Significant risk detected."

        return {
            "composite": total,
            "breakdown": {
                "technical": t_score,
                "fundamental": f_score,
                "macro": m_score,
            },
            "max_scores": self.weights,
            "verdict": verdict,
            "conviction": conviction,
            "action": action,
        }
