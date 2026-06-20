"""
Central config. Reads from a .env file (never committed) or the environment.
Copy .env.example -> .env and fill in your values.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # loads .env from the project root if present

# --- Supabase ---
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# --- News ---
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

# --- IBKR (paper) ---
IBKR_API_HOST = os.getenv("IBKR_API_HOST", "127.0.0.1")
IBKR_API_PORT = int(os.getenv("IBKR_API_PORT", "4002"))  # 4002 = paper gateway


def require(*names: str) -> None:
    """Raise a clear error if a needed env var is missing."""
    missing = [n for n in names if not globals().get(n)]
    if missing:
        raise SystemExit(
            "Missing config: " + ", ".join(missing) +
            "\nFill them into your .env file (see .env.example)."
        )
