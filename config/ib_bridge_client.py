# config/ib_bridge_client.py
import os

def get_bridge_url() -> str:
    """
    Returns the IBKR Bridge base URL from env. Supports both old/new var names.
    Falls back to a sane default if not set.
    """
    return (
        os.getenv("IBKR_BRIDGE_URL")
        or os.getenv("IB_BRIDGE_URL")
        or "http://167.71.145.48:8088"
    ).rstrip("/")

def get_bridge_api_key() -> str:
    """
    Returns the API key header value required by the user's bridge.
    """
    return (
        os.getenv("IB_BRIDGE_API_KEY")
        or os.getenv("BRIDGE_API_KEY")
        or ""
    )