import json
import os

import redis


class RedisJobQueue:
    def __init__(self):
        redis_url = os.getenv(
            "REDIS_URL",
            "redis://localhost:6379/0",
        )

        self.redis = redis.from_url(
            redis_url,
            decode_responses=True,
        )

        self.queue_name = "cv_jobs"

    def submit(self, job):
        self.redis.rpush(
            self.queue_name,
            json.dumps(job),
        )
