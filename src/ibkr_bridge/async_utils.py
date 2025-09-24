# src/ibkr_bridge/async_utils.py
import asyncio
import nest_asyncio

def ensure_loop():
    """
    Ensure there is an event loop usable from Streamlit's ScriptRunner thread.
    Applies nest_asyncio so ib_insync/EventKit coroutines can run safely.
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    # idempotent: safe to call multiple times
    nest_asyncio.apply(loop)
    return loop

def run(coro):
    """
    Run an async coroutine to completion, returning its result.
    Example: run(ib.connectAsync(host, port, clientId=1))
    """
    loop = ensure_loop()
    return loop.run_until_complete(coro)

