"""Long-running Temporal worker — the durable piece of the platform.

This is a separate, long-lived service (NOT a serverless function): it connects
to Temporal and polls a task queue for the life of the process. Temporal's
`auto-setup` image needs ~20-30s before it accepts connections, so we retry with
exponential backoff rather than crashing on first failure.

Only stubbed agent activities are registered at Milestone 0 — the deal-lifecycle
workflow and real activities land later (see PLAN.md).
"""
import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from app.config import TASK_QUEUE, TEMPORAL_ADDRESS
from worker.activities import stub_agent_activity

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("worker")


async def connect_with_retry(
    address: str,
    *,
    max_attempts: int = 60,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
) -> Client:
    """Connect to Temporal, retrying with exponential backoff.

    Survives the ~20-30s `temporalio/auto-setup` startup window instead of
    crash-looping on the first refused connection.
    """
    delay = initial_delay
    last_err: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            client = await Client.connect(address)
            log.info("Connected to Temporal at %s (attempt %d)", address, attempt)
            return client
        except Exception as err:  # noqa: BLE001 - retry on any connect failure
            last_err = err
            log.warning(
                "Temporal not ready at %s (attempt %d/%d): %s; retrying in %.0fs",
                address, attempt, max_attempts, err, delay,
            )
            await asyncio.sleep(delay)
            delay = min(delay * 2, max_delay)
    raise RuntimeError(
        f"Could not connect to Temporal at {address} after {max_attempts} attempts"
    ) from last_err


async def main() -> None:
    client = await connect_with_retry(TEMPORAL_ADDRESS)
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        activities=[stub_agent_activity],
    )
    log.info("Worker started; polling task queue %r", TASK_QUEUE)
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
