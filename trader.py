# ============================================================
# TRADER - Handles all Polymarket API calls via Relayer
# ============================================================

import requests
import time
import logging
from config import (
    GAMMA_API, CLOB_API, DATA_API,
    RELAYER_API_KEY, RELAYER_API_KEY_ADDRESS,
    FOCUS_CATEGORIES, STARTING_BALANCE
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TRADER")

RELAYER_API = "RELAYER_API = "https://clob.polymarket.com""

class PolymarketTrader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "RELAYER_API_KEY": RELAYER_API_KEY,
            "RELAYER_API_KEY_ADDRESS": RELAYER_API_KEY_ADDRESS
        })
        self.balance = STARTING_BALANCE
        self.total_profit = 0.0
        self.trades_placed = 0
        self.wins = 0
        self.losses = 0
        logger.info(f"✅ Trader initialized with balance: ${self.balance}")

    def get_balance(self) -> float:
        """Get balance via Relayer API - no geoblock."""
        try:
            url = f"{RELAYER_API}/balance"
            headers = {
                "RELAYER_API_KEY": RELAYER_API_KEY,
                "RELAYER_API_KEY_ADDRESS": RELAYER_API_KEY_ADDRESS
            }
            response = self.session.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                balance = float(data.get("balance", 0))
                if balance > 0:
                    self.balance = balance
                    return balance
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
        return self.balance

    def get_sports_markets(self) -> list:
        """Fetch markets - Gamma API has no geoblock."""
        all_markets = []
        try:
            for category in FOCUS_CATEGORIES:
                url = f"{GAMMA_API}/markets"
                params = {
                    "active": "true",
                    "closed": "false",
                    "tag_slug": category,
                    "limit": 100
                }
                response = self.session.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    markets = data if isinstance(data, list) else data.get("markets", [])
                    all_markets.extend(markets)
                    logger.info(f"Found {len(markets)} {category} markets")
                time.sleep(0.5)

            url = f"{GAMMA_API}/markets"
            params = {"active": "true", "closed": "false", "limit": 200, "order": "volume24hr", "ascending": "false"}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                markets = data if isinstance(data, list) else data.get("markets", [])
                all_markets.extend(markets)

            seen = set()
            unique = []
            for m in all_markets:
                mid = m.get("id")
                if mid and mid not in seen:
                    seen.add(mid)
                    unique.append(m)

            logger.info(f"Total unique markets found: {len(unique)}")
            return unique

        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []

    def place_market_order(self, token_id: str, amount: float, side: str = "BUY") -> dict:
        """Place order via Relayer API - bypasses geoblock."""
        try:
            url = f"{RELAYER_API}/order"
            order_data = {
                "tokenId": token_id,
                "side": side,
                "amount": str(amount),
                "type": "MARKET"
            }
            headers = {
                "Content-Type": "application/json",
                "RELAYER_API_KEY": RELAYER_API_KEY,
                "RELAYER_API_KEY_ADDRESS": RELAYER_API_KEY_ADDRESS
            }
            response = self.session.post(url, json=order_data, headers=headers, timeout=15)
            if response.status_code == 200:
                self.trades_placed += 1
                logger.info(f"✅ Order placed: {side} ${amount}")
                return response.json()
            else:
                logger.error(f"Order failed: {response.status_code} - {response.text}")
                return {"error": response.text}
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"error": str(e)}

    def get_positions(self) -> list:
        try:
            url = f"{DATA_API}/positions"
            params = {"user": RELAYER_API_KEY_ADDRESS, "sizeThreshold": 0.01}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error getting positions: {e}")
        return []

    def get_trade_history(self) -> list:
        try:
            url = f"{DATA_API}/activity"
            params = {"user": RELAYER_API_KEY_ADDRESS, "limit": 50}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
        return []

    def get_top_trader_positions(self) -> list:
        top_traders = [
            "0xee613b3fc183ee44f9da9c05f53e2da107e3debf",
        ]
        signals = []
        try:
            for trader in top_traders:
                url = f"{DATA_API}/positions"
                params = {"user": trader, "sizeThreshold": 10}
                response = self.session.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    positions = response.json()
                    for pos in positions:
                        signals.append({
                            "trader": trader[:10],
                            "market_id": pos.get("market", ""),
                            "outcome": pos.get("outcome", ""),
                            "size": pos.get("size", 0),
                            "avg_price": pos.get("avgPrice", 0),
                            "signal": "MIRROR"
                        })
                time.sleep(0.5)
        except Exception as e:
            logger.error(f"Error getting top trader positions: {e}")
        return signals
