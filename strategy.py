# ============================================================
# STRATEGY ENGINE - Sovereign2013 Style Sports Arbitrage
# ============================================================

import math
from config import (
    MIN_EDGE, MIN_LIQUIDITY, MAX_PRICE, MIN_PRICE,
    KELLY_FRACTION, MAX_BET_PERCENT, MIN_BET_AMOUNT, MAX_BET_AMOUNT
)


def implied_probability(price: float) -> float:
    """Convert market price to implied probability."""
    return price


def calculate_edge(market_price: float, true_probability: float) -> float:
    """Calculate our edge over the market."""
    return true_probability - market_price


def kelly_bet_size(edge: float, price: float, balance: float) -> float:
    """
    Kelly Criterion - mathematically optimal bet sizing.
    Used by sovereign2013 to compound aggressively.
    f = (bp - q) / b
    where b = odds-1, p = true prob, q = 1-p
    """
    if price <= 0 or price >= 1:
        return 0

    b = (1 / price) - 1  # decimal odds minus 1
    p = price + edge      # our estimated true probability
    q = 1 - p

    kelly = (b * p - q) / b
    fractional_kelly = kelly * KELLY_FRACTION  # Quarter Kelly for safety

    # Apply limits
    bet = balance * fractional_kelly
    bet = max(MIN_BET_AMOUNT, min(MAX_BET_AMOUNT, bet))
    bet = min(bet, balance * MAX_BET_PERCENT)

    return round(bet, 2)


def estimate_true_probability(market: dict) -> float:
    """
    Estimate the TRUE probability of an outcome.
    This is our edge engine - where we beat the market.

    Strategy layers (sovereign2013 style):
    1. Recent form analysis via market movement
    2. Liquidity imbalance detection
    3. Late market correction exploitation
    4. Cross-market arbitrage signals
    """
    price = market.get("price", 0.5)
    volume = market.get("volume", 0)
    liquidity = market.get("liquidity", 0)
    price_change = market.get("price_change_24h", 0)

    estimated_prob = price  # Start with market price

    # Signal 1: Heavy volume with low price = undervalued YES
    if volume > 10000 and price < 0.4:
        estimated_prob += 0.04

    # Signal 2: Price dropped sharply but recovering = bounce play
    if price_change < -0.1 and price < 0.5:
        estimated_prob += 0.03

    # Signal 3: Thin liquidity on heavily favored side = fade the public
    if liquidity < 500 and price > 0.7:
        estimated_prob -= 0.05  # Fade the heavy favourite

    # Signal 4: Price moving up fast = momentum play
    if price_change > 0.05 and price < 0.6:
        estimated_prob += 0.02

    # Signal 5: Near resolution with high certainty mispricing
    if price < 0.15 and volume > 5000:
        estimated_prob += 0.05  # Underdog value

    return max(0.01, min(0.99, estimated_prob))


def analyze_market(market: dict, balance: float) -> dict | None:
    """
    Full market analysis. Returns trade signal or None.
    This is the core brain of the bot.
    """
    try:
        price = float(market.get("outcomePrices", ["0.5"])[0])
        liquidity = float(market.get("liquidity", 0))
        volume = float(market.get("volume", 0))
        active = market.get("active", False)
        closed = market.get("closed", True)

        # Skip invalid markets
        if not active or closed:
            return None
        if price <= MIN_PRICE or price >= MAX_PRICE:
            return None
        if liquidity < MIN_LIQUIDITY:
            return None

        # Build market data for analysis
        market_data = {
            "price": price,
            "volume": volume,
            "liquidity": liquidity,
            "price_change_24h": float(market.get("lastTradePrice", price)) - price
        }

        true_prob = estimate_true_probability(market_data)
        edge = calculate_edge(price, true_prob)

        if edge < MIN_EDGE:
            return None

        bet_size = kelly_bet_size(edge, price, balance)

        if bet_size < MIN_BET_AMOUNT:
            return None

        return {
            "market_id": market.get("id"),
            "question": market.get("question", "Unknown"),
            "token_id": market.get("clobTokenIds", [""])[0],
            "price": price,
            "true_prob": true_prob,
            "edge": edge,
            "bet_size": bet_size,
            "liquidity": liquidity,
            "volume": volume,
            "outcome": "YES",
            "confidence": "HIGH" if edge > 0.07 else "MEDIUM"
        }

    except Exception as e:
        return None


def rank_opportunities(opportunities: list) -> list:
    """Rank opportunities by expected value. Best first."""
    def expected_value(opp):
        return opp["edge"] * opp["bet_size"]

    return sorted(opportunities, key=expected_value, reverse=True)
