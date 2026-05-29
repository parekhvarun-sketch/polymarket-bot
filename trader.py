# ============================================================
# TRADER - Handles all Polymarket API calls
# ============================================================

import requests
import json
import time
import logging
from config import (
    GAMMA_API, CLOB_API, DATA_API,
    RELAYER_API_KEY, RELAYER_API_KEY_ADDRESS,
    FOCUS_CATEGORIES
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TRADER")


class PolymarketTrader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "RELAYER_API_KEY": RELAYER_API_KEY,
            "RELAYER_API_KEY_ADDRESS": RELAYER_API_KEY_ADDRESS
        })
        self.balance = 0.0
        self.total_profit = 0.0
        self.trades_placed = 0
        self.wins = 0
        self.losses = 0

    # ----------------------------------------------------------
    # MARKET SCANNING
    # ----------------------------------------------------------

    def get_sports_markets(self) -> list:
        """Fetch all active sports markets from Gamma API."""
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

            # Also get trending/breaking markets
            url = f"{GAMMA_API}/markets"
            params = {"active": "true", "closed": "false", "limit": 200, "order": "volume24hr", "ascending": "false"}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                markets = data if isinstance(data, list) else data.get("markets", [])
                all_markets.extend(markets)

            # Remove duplicates
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

    def get_market_price(self, token_id: str) -> float:
        """Get current best price for a token."""
        try:
            url = f"{CLOB_API}/price"
            params = {"token_id": token_id, "side": "buy"}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return float(data.get("price", 0))
        except Exception as e:
            logger.error(f"Error getting price: {e}")
        return 0.0

    def get_orderbook(self, token_id: str) -> dict:
        """Get full orderbook for a market."""
        try:
            url = f"{CLOB_API}/book"
            params = {"token_id": token_id}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error getting orderbook: {e}")
        return {}

    def get_balance(self) -> float:
        """Get current USDC balance."""
        try:
            url = f"{CLOB_API}/balance-allowance"
            params = {"asset_type": "USDC", "signature_type": 0}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                balance = float(data.get("balance", 0)) / 1e6  # Convert from micro
                self.balance = balance
                return balance
        except Exception as e:
            logger.error(f"Error getting balance: {e}")
        return self.balance

    # ----------------------------------------------------------
    # ORDER PLACEMENT
    # ----------------------------------------------------------

    def place_market_order(self, token_id: str, amount: float, side: str = "BUY") -> dict:
        """
        Place a market order via Relayer API.
        side: BUY (betting YES) or SELL
        amount: in USDC
        """
        try:
            url = f"{CLOB_API}/order"
            order_data = {
                "order": {
                    "tokenId": token_id,
                    "side": side,
                    "price": 0,  # Market order
                    "size": str(int(amount * 1e6)),  # Convert to micro USDC
                    "type": "MARKET"
                }
            }
            response = self.session.post(url, json=order_data, timeout=15)
            if response.status_code == 200:
                result = response.json()
                self.trades_placed += 1
                logger.info(f"✅ Order placed: {side} ${amount} on token {token_id[:8]}...")
                return result
            else:
                logger.error(f"Order failed: {response.status_code} - {response.text}")
                return {"error": response.text}

        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return {"error": str(e)}

    def get_positions(self) -> list:
        """Get all current open positions."""
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
        """Get completed trades."""
        try:
            url = f"{DATA_API}/activity"
            params = {"user": RELAYER_API_KEY_ADDRESS, "limit": 50}
            response = self.session.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error getting trade history: {e}")
        return []

    # ----------------------------------------------------------
    # TOP TRADER MIRRORING (sovereign2013 style)
    # ----------------------------------------------------------

    def get_top_trader_positions(self) -> list:
        """
        Mirror top traders - watch what sovereign2013 and others are betting on.
        """
        top_traders = [
            "0xee613b3fc183ee44f9da9c05f53e2da107e3debf",  # sovereign2013
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
