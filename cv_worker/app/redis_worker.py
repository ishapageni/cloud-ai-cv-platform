import json
import os
import shutil
import tempfile
import time
import uuid
from datetime import datetime, timezone

import redis

from cv_worker.app.worker import CVWorker
from backend.app.db.database import SessionLocal
from backend.app.db.models import Job
from backend.app.services.storage import download_file


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)

QUEUE_NAME = "cv_jobs"


redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
)

worker = CVWorker()


print("CV worker started.")
print(f"Listening on Redis queue: {QUEUE_NAME}")


def update_job_status(
    job_id: str,
    status: str,
):
    """
    Update the job lifecycle state in PostgreSQL.
    """

    db = SessionLocal()

    try:
        job = db.get(
            Job,
            uuid.UUID(job_id),
        )

        if not job:
            print(
                f"Job not found in database: {job_id}"
            )
            return

        job.status = status

        db.commit()

        print(
            f"Job {job_id} status → {status}"
        )

    except Exception as error:
        db.rollback()

        print(
            f"Failed to update job {job_id} "
            f"status to {status}: {error}"
        )

    finally:
        db.close()


while True:

    item = redis_client.brpop(
        QUEUE_NAME,
        timeout=5,
    )

    if item is None:
        continue

    _, payload = item

    job = json.loads(payload)

    job_id = job["job_id"]

    print(
        f"Processing job: {job_id}"
    )

    temp_dir = None

    try:

        # ----------------------------------------
        # queued → processing
        # ----------------------------------------

        update_job_status(
            job_id,
            "processing",
        )

        # ----------------------------------------
        # Create temporary job directory
        # ----------------------------------------

        temp_dir = tempfile.mkdtemp(
            prefix=f"cloud-ai-cv-{job_id}-"
        )

        input_path = os.path.join(
            temp_dir,
            "input.jpg",
        )

        result_dir = os.path.join(
            temp_dir,
            "results",
        )

        os.makedirs(
            result_dir,
            exist_ok=True,
        )

        # ----------------------------------------
        # Download input from object storage
        # ----------------------------------------

        input_object_key = job[
            "input_object_key"
        ]

        download_file(
            input_object_key,
            input_path,
        )

        # ----------------------------------------
        # Build worker job
        # ----------------------------------------

        worker_job = {
            **job,
            "image_path": input_path,
            "result_dir": result_dir,
        }

        # ----------------------------------------
        # Run computer vision inference
        # ----------------------------------------

        result = worker.process(
            worker_job
        )

        # ----------------------------------------
        # Send result back to API
        # ----------------------------------------

        redis_client.rpush(
            f"cv_results:{job_id}",
            json.dumps(result),
        )

        print(
            f"Completed job: {job_id}"
        )

    except Exception as error:

        print(
            f"Worker error for {job_id}: {error}"
        )

        # ----------------------------------------
        # processing → failed
        # ----------------------------------------

        update_job_status(
            job_id,
            "failed",
        )

        failure_result = {
            "job_id": job_id,
            "status": "failed",
            "error": str(error),
            "completed_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        redis_client.rpush(
            f"cv_results:{job_id}",
            json.dumps(failure_result),
        )

    finally:

        # ----------------------------------------
        # Always clean up temporary files
        # ----------------------------------------

        if temp_dir and os.path.exists(
            temp_dir
        ):
            try:

                shutil.rmtree(
                    temp_dir
                )

                print(
                    f"Cleaned temporary files "
                    f"for job {job_id}"
                )

            except Exception as cleanup_error:

                print(
                    f"Temporary cleanup failed "
                    f"for job {job_id}: "
                    f"{cleanup_error}"
                )

    time.sleep(0.1)
