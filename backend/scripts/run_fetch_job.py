import asyncio
import sys
from uuid import UUID

from app.services.fetch_queue import _run_job


async def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: run_fetch_job.py <job_id>")
    job_id = UUID(sys.argv[1])
    await _run_job(job_id)


if __name__ == "__main__":
    asyncio.run(main())
