# utils/preload_asyncio.py

import asyncio

# 👇 Force event loop before anything else
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())
# 🧠