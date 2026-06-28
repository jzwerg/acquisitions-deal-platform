"""Worker entrypoint sanity checks (no Temporal server required)."""
import asyncio

from app import config
from worker.activities import stub_agent_activity


def test_worker_entrypoint_is_importable():
    import worker.__main__ as entry

    assert callable(entry.main)
    assert callable(entry.connect_with_retry)


def test_stub_activity_returns_mock_without_api_key():
    # Milestone 0 boots with LLM_MOCK=true and no ANTHROPIC_API_KEY.
    assert config.LLM_MOCK is True
    result = asyncio.run(stub_agent_activity("hello"))
    assert "[mock]" in result
