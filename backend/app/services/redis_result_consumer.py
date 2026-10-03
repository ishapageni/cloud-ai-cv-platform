import json
import os
import threading
from datetime import datetime, timezone

import redis

from backend.app.db.database import SessionLocal
from backend.app.db.models import Detection, Job


REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://localhost:6379/0",
)


redis_client = redis.from_url(
    REDIS_URL,
    decode_responses=True,
)


def save_result(result):
    db = SessionLocal()

    try:
        job_id = result["job_id"]

        job = db.get(
            Job,
            job_id,
        )

        if not job:
            print(
                f"Job not found: {job_id}"
            )
            return

        status = result.get(
            "status",
            "completed",
        )

        # ----------------------------------------
        # Failed job
        # ----------------------------------------

        if status == "failed":

            job.status = "failed"

            job.completed_at = datetime.now(
                timezone.utc
            )

            db.commit()

            print(
                f"Saved failed job: {job_id}"
            )

            return

        # ----------------------------------------
        # Completed job
        # ----------------------------------------

        job.status = "completed"

        job.completed_at = datetime.now(
            timezone.utc
        )

        job.result_object_key = result.get(
            "result_object_key"
        )

        detections = result.get(
            "detections",
            [],
        )

        for detection in detections:

            box = detection[
                "bounding_box"
            ]

            db.add(
                Detection(
                    job_id=job_id,
                    class_id=detection[
                        "class_id"
                    ],
                    class_name=detection[
                        "class_name"
                    ],
                    confidence=detection[
                        "confidence"
                    ],
                    x1=box["x1"],
                    y1=box["y1"],
                    x2=box["x2"],
                    y2=box["y2"],
                )
            )

        db.commit()

        print(
            f"Saved result for job {job_id}: "
            f"{len(detections)} detections"
        )

    except Exception as error:

        db.rollback()

        print(
            f"Result save error: {error}"
        )

    finally:
        db.close()


def consume_results():

    while True:

        keys = redis_client.keys(
            "cv_results:*"
        )

        for key in keys:

            item = redis_client.lpop(
                key
            )

            if item is None:
                continue

            try:

                result = json.loads(
                    item
                )

                save_result(
                    result
                )

                redis_client.delete(
                    key
                )

            except Exception as error:

                print(
                    f"Redis result error: {error}"
                )


def start_result_consumer():

    print(
        "Starting Redis result consumer..."
    )

    thread = threading.Thread(
        target=consume_results,
        daemon=True,
    )

    thread.start()

    print(
        "Redis result consumer started."
    )
