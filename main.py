#!/usr/bin/env python3
# ============================================================
# POLYMARKET KILLER BOT
# Strategy: sovereign2013 + frankfrankfrank + ascetic0x
# Runs 24/7, compounds aggressively, mirrors top traders
# ============================================================

import time
import logging
import json
from datetime import datetime
from trader import PolymarketTrader
from strategy import analyze_market, rank_opportunities
from config import (
    SCAN_INTERVAL, STOP_LOSS_PERCENT,
    STARTING_BALANCE, MIN_BET_AMOUNT
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("BOT")


def print_banner():
    print("""
╔══════════════════════════════════════════╗
║       POLYMARKET KILLER BOT 🔥           ║
║   Strategy: sovereign2013 + Top Traders  ║
║   Mode: AGGRESSIVE | 24/7 AUTO-COMPOUND  ║
╚══════════════════════════════════════════╝
    """)


def print_stats(bot: PolymarketTrader, cycle: int):
    balance = bot.balance
    profit = balance - STARTING_BALANCE
    profit_pct = (profit / STARTING_BALANCE) * 100 if STARTING_BALANCE > 0 else 0
    win_rate = (bot.wins / bot.trades_placed * 100) if bot.trades_placed > 0 else 0

    print(f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 CYCLE #{cycle} | {datetime.now().strftime('%H:%M:%S')}
💰 Balance:     ${balance:.2f}
📈 Profit:      ${profit:.2f} ({profit_pct:.1f}%)
🎯 Trades:      {bot.trades_placed}
✅ Wins:        {bot.wins}
❌ Losses:      {bot.losses}
🏆 Win Rate:    {win_rate:.1f}%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)


def save_state(bot: PolymarketTrader, opportunities: list):
    """Save bot state to file for monitoring."""
    state = {
        "timestamp": datetime.now().isoformat(),
        "balance": bot.balance,
        "profit": bot.balance - STARTING_BALANCE,
        "trades_placed": bot.trades_placed,
        "wins": bot.wins,
        "losses": bot.losses,
        "last_opportunities": len(opportunities)
    }
    with open("bot_state.json", "w") as f:
        json.dump(state, f, indent=2)


def check_stop_loss(bot: PolymarketTrader) -> bool:
    """Stop bot if balance drops below stop loss threshold."""
    stop_loss_amount = STARTING_BALANCE * STOP_LOSS_PERCENT
    if bot.balance < stop_loss_amount and bot.balance > 0:
        logger.warning(f"⛔ STOP LOSS HIT! Balance ${bot.balance:.2f} below ${stop_loss_amount:.2f}")
        return True
    return False


def run_mirror_strategy(bot: PolymarketTrader):
    """
    Mirror sovereign2013 and other top traders.
    If they're betting on something - we bet on it too.
    """
    logger.info("🔍 Checking top trader positions...")
    signals = bot.get_top_trader_positions()

    if not signals:
        return

    balance = bot.balance
    for signal in signals[:3]:  # Top 3 signals max per cycle
        if balance < MIN_BET_AMOUNT:
            break

        bet_size = min(balance * 0.10, 2.0)  # 10% or max $2 for mirror trades

        logger.info(f"📡 MIRROR SIGNAL: {signal['trader']}... betting {signal['outcome']} @ {signal['avg_price']}")

        if bet_size >= MIN_BET_AMOUNT:
            result = bot.place_market_order(
                token_id=signal["market_id"],
                amount=bet_size,
                side="BUY"
            )
            if "error" not in result:
                logger.info(f"✅ Mirror trade placed: ${bet_size:.2f}")
            time.sleep(1)


def run_arbitrage_strategy(bot: PolymarketTrader):
    """
    Core arbitrage strategy - find mispriced markets and bet.
    sovereign2013 style - rapid fire, high volume.
    """
    logger.info("🔍 Scanning sports markets for mispriced odds...")

    markets = bot.get_sports_markets()
    if not markets:
        logger.warning("No markets found this cycle")
        return

    balance = bot.balance
    opportunities = []

    for market in markets:
        opp = analyze_market(market, balance)
        if opp:
            opportunities.append(opp)

    opportunities = rank_opportunities(opportunities)
    logger.info(f"🎯 Found {len(opportunities)} opportunities")

    # Save state
    save_state(bot, opportunities)

    if not opportunities:
        return

    # Execute top opportunities
    max_trades_per_cycle = 5  # Aggressive - up to 5 trades per scan
    trades_this_cycle = 0

    for opp in opportunities[:max_trades_per_cycle]:
        if balance < MIN_BET_AMOUNT:
            logger.warning("Balance too low to trade")
            break

        logger.info(f"""
🎲 OPPORTUNITY FOUND:
   Market: {opp['question'][:60]}
   Price:  {opp['price']:.3f} | True Prob: {opp['true_prob']:.3f}
   Edge:   {opp['edge']:.1%} | Confidence: {opp['confidence']}
   Bet:    ${opp['bet_size']:.2f}
        """)

        result = bot.place_market_order(
            token_id=opp["token_id"],
            amount=opp["bet_size"],
            side="BUY"
        )

        if "error" not in result:
            balance -= opp["bet_size"]
            trades_this_cycle += 1
            logger.info(f"✅ Trade #{bot.trades_placed} executed!")
        else:
            logger.error(f"❌ Trade failed: {result.get('error', 'Unknown')}")

        time.sleep(2)  # Small delay between orders

    return opportunities


def main():
    print_banner()
    logger.info("🚀 Bot starting up...")

    bot = PolymarketTrader()

    # Get initial balance
    balance = bot.get_balance()
    if balance == 0:
        logger.warning("⚠️  Balance is $0. Make sure funds are deposited in Polymarket!")
        logger.info("Bot will keep checking every 60 seconds until funds appear...")

    logger.info(f"💰 Starting balance: ${balance:.2f}")
    logger.info(f"🔥 Scanning every {SCAN_INTERVAL} seconds")
    logger.info("=" * 50)

    cycle = 0

    while True:
        try:
            cycle += 1

            # Refresh balance
            bot.get_balance()

            # Print stats every 10 cycles
            if cycle % 10 == 1:
                print_stats(bot, cycle)

            # Check stop loss
            if check_stop_loss(bot):
                logger.warning("Bot paused due to stop loss. Check your positions.")
                time.sleep(300)  # Wait 5 mins then recheck
                continue

            # Skip if no balance
            if bot.balance < MIN_BET_AMOUNT:
                logger.info(f"⏳ Balance ${bot.balance:.2f} too low. Waiting for funds or wins to compound...")
                time.sleep(60)
                continue

            # Run core strategies
            # Strategy 1: Arbitrage (primary - sovereign2013 style)
            run_arbitrage_strategy(bot)

            # Strategy 2: Mirror top traders (secondary signal)
            if cycle % 5 == 0:  # Every 5th cycle
                run_mirror_strategy(bot)

            logger.info(f"⏱️  Next scan in {SCAN_INTERVAL} seconds...")
            time.sleep(SCAN_INTERVAL)

        except KeyboardInterrupt:
            logger.info("🛑 Bot stopped by user")
            print_stats(bot, cycle)
            break

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            logger.info("Restarting in 60 seconds...")
            time.sleep(60)


if __name__ == "__main__":
    main()
