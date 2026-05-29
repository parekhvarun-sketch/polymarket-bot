============================================================
POLYMARKET KILLER BOT - SETUP GUIDE
============================================================

STEP 1 - ADD YOUR CREDENTIALS
------------------------------
Open config.py and fill in:
  RELAYER_API_KEY = "your api key from Polymarket"
  RELAYER_API_KEY_ADDRESS = "your wallet address from Polymarket"

STEP 2 - DEPLOY TO RAILWAY (Free Cloud)
----------------------------------------
1. Go to railway.app
2. Sign up with GitHub (free)
3. Click "New Project"
4. Click "Deploy from GitHub repo"
5. Upload these files OR use "Deploy from template"
6. Add environment variables:
   - RELAYER_API_KEY = your key
   - RELAYER_API_KEY_ADDRESS = your address
7. Click Deploy
8. Bot runs 24/7 automatically!

STEP 3 - MONITOR
-----------------
- Bot prints stats every 10 cycles
- Check bot_state.json for current status
- Bot auto-stops if balance drops 50%

WHAT THE BOT DOES
------------------
Every 30 seconds:
1. Scans all sports markets on Polymarket
2. Finds mispriced odds (our edge)
3. Bets using Kelly Criterion sizing
4. Mirrors sovereign2013 positions
5. Compounds all winnings automatically

STRATEGY
---------
- Focus: Sports markets (basketball, football, soccer, tennis)
- Style: sovereign2013 arbitrage + top trader mirroring
- Risk: Max 20% of balance per bet
- Stop Loss: Pauses if balance drops 50%

FILES
------
main.py      - Main bot runner
config.py    - Your settings (edit this!)
strategy.py  - Trading brain / edge detection
trader.py    - Polymarket API handler
requirements.txt - Python packages needed
Procfile     - Railway deployment config

============================================================
