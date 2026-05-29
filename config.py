# ============================================================
# POLYMARKET BOT - CONFIGURATION
# ============================================================
# Fill in your details below before running

# --- YOUR CREDENTIALS (from Polymarket Relayer API Keys page) ---
RELAYER_API_KEY = "YOUR_API_KEY_HERE"           # e.g. 019e48fa-346c-...
RELAYER_API_KEY_ADDRESS = "YOUR_WALLET_ADDRESS" # e.g. 0x2C2D61...

# --- STARTING BALANCE (in USDC) ---
STARTING_BALANCE = 12.0  # ~₹1000

# --- RISK MANAGEMENT ---
MAX_BET_PERCENT = 0.20       # Max 20% of balance per bet
MIN_BET_AMOUNT = 0.50        # Minimum $0.50 per bet
MAX_BET_AMOUNT = 5.00        # Maximum $5 per bet (scales as balance grows)
STOP_LOSS_PERCENT = 0.50     # Stop bot if balance drops below 50% of start
KELLY_FRACTION = 0.25        # Quarter Kelly - aggressive but not suicidal

# --- STRATEGY SETTINGS ---
MIN_EDGE = 0.03              # Minimum 3% edge to place bet
MIN_LIQUIDITY = 100          # Minimum $100 liquidity in market
MAX_PRICE = 0.95             # Don't bet on near-certainties
MIN_PRICE = 0.05             # Don't bet on near-impossibilities
SCAN_INTERVAL = 30           # Scan markets every 30 seconds
FOCUS_CATEGORIES = [         # sovereign2013 style - sports focus
    "sports",
    "basketball",
    "football",
    "soccer",
    "tennis",
    "baseball",
    "cricket"
]

# --- API ENDPOINTS ---
GAMMA_API = "https://gamma-api.polymarket.com"
CLOB_API  = "https://clob.polymarket.com"
DATA_API  = "https://data-api.polymarket.com"
