"""Cached Temporal client for the API process.

The API talks to Temporal to start deals and send human-approval signals. We
connect lazily (with a short retry) and cache one client — Temporal may still be
warming up when the API first serves.
"""
from __future__ import annotations

import asyncio

from temporalio.client import Client

from app import config

_client: Client | None = None
_lock = asyncio.Lock()


async def get_client() -> Client:
    global _client
    async with _lock:
        if _client is None:
            delay = 1.0
            last_err: Exception | None = None
            for _ in range(10):
                try:
                    _client = await Client.connect(config.TEMPORAL_ADDRESS)
                    break
                except Exception as err:  # noqa: BLE001 - retry on any connect failure
                    last_err = err
                    await asyncio.sleep(delay)
                    delay = min(delay * 2, 5.0)
            else:
                raise RuntimeError(
                    f"Could not connect to Temporal at {config.TEMPORAL_ADDRESS}"
                ) from last_err
    return _client
