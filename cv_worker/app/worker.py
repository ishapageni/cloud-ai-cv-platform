import os
import tempfile

from PIL import Image

from cv_worker.app.detector import CVDetector
from backend.app.services.storage import upload_file


class CVWorker:
    def __init__(self):
        self.detector = CVDetector()

    def process(self, job):
        job_id = job["job_id"]
        image_path = job["image_path"]

        result_dir = job.get(
            "result_dir",
            tempfile.gettempdir(),
        )

        os.makedirs(
            result_dir,
            exist_ok=True,
        )

        detections, annotated = self.detector.predict(
            image_path
        )

        result_path = os.path.join(
            result_dir,
            f"{job_id}_result.jpg",
        )

        # YOLO plot() returns BGR.
        # PIL expects RGB.
        Image.fromarray(
            annotated[:, :, ::-1]
        ).save(
            result_path,
            format="JPEG",
        )

        result_object_key = (
            f"results/{job_id}_result.jpg"
        )

        upload_file(
            result_path,
            result_object_key,
            "image/jpeg",
        )

        return {
            "job_id": job_id,
            "status": "completed",
            "detections": detections,
            "detection_count": len(detections),
            "result_path": result_path,
            "result_object_key": result_object_key,
        }
