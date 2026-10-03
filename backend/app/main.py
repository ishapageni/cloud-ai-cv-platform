from datetime import datetime, timezone
import os
import shutil
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.app.db.database import SessionLocal
from backend.app.db.models import Detection, Job
from backend.app.services.redis_queue import RedisJobQueue
from backend.app.services.redis_result_consumer import start_result_consumer
from backend.app.services.storage import get_object, upload_file


app = FastAPI(
    title="Cloud AI/CV Platform",
    description="Computer vision inference platform",
    version="0.6.0",
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Directories
# --------------------------------------------------

UPLOAD_DIR = "backend/uploads"
RESULT_DIR = "backend/results"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RESULT_DIR, exist_ok=True)


# --------------------------------------------------
# Services
# --------------------------------------------------

start_result_consumer()

job_queue = RedisJobQueue()


# --------------------------------------------------
# Health
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "cloud-ai-cv-backend",
    }


# --------------------------------------------------
# Submit prediction job
# --------------------------------------------------
# --------------------------------------------------
# Get job history
# --------------------------------------------------

@app.get("/jobs")
def get_jobs():

    db: Session = SessionLocal()

    try:
        jobs = (
            db.query(Job)
            .order_by(
                Job.created_at.desc()
            )
            .all()
        )

        return [
            {
                "job_id": str(job.job_id),
                "filename": job.filename,
                "status": job.status,
                "model": job.model,
                "created_at": (
                    job.created_at.isoformat()
                    if job.created_at
                    else None
                ),
                "completed_at": (
                    job.completed_at.isoformat()
                    if job.completed_at
                    else None
                ),
                "result_object_key": (
                    job.result_object_key
                ),
            }
            for job in jobs
        ]

    finally:
        db.close()

@app.post("/predict")
async def predict(file: UploadFile = File(...)):

    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Unsupported image type. Use JPEG, PNG, or WebP.",
        )

    job_id = uuid.uuid4()

    extension = allowed_types[file.content_type]

    input_filename = f"{job_id}{extension}"

    input_path = os.path.join(
        UPLOAD_DIR,
        input_filename,
    )

    # Save temporary local copy.
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer,
        )

    # Store original input in object storage.
    input_object_key = (
        f"inputs/{input_filename}"
    )

    try:
        upload_file(
            input_path,
            input_object_key,
            file.content_type,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Object storage upload failed: {error}",
        )

    finally:
        if os.path.exists(input_path):
            os.remove(input_path)

    # Create database job.
    db: Session = SessionLocal()

    try:
        job = Job(
            job_id=job_id,
            filename=file.filename or input_filename,
            status="queued",
            model="YOLO11n",
        )

        db.add(job)
        db.commit()

    except Exception as error:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {error}",
        )

    finally:
        db.close()

    # Submit asynchronous job.
    try:
        job_queue.submit(
            {
                "job_id": str(job_id),
                "input_object_key": input_object_key,
            }
        )

    except Exception as error:

        db = SessionLocal()

        try:
            failed_job = db.get(
                Job,
                job_id,
            )

            if failed_job:
                failed_job.status = "failed"
                db.commit()

        finally:
            db.close()

        raise HTTPException(
            status_code=500,
            detail=f"Queue submission failed: {error}",
        )

    return {
        "job_id": str(job_id),
        "status": "queued",
        "filename": file.filename,
        "model": "YOLO11n",
    }


# --------------------------------------------------
# Get job
# --------------------------------------------------

@app.get("/jobs/{job_id}")
def get_job(job_id: str):

    try:
        job_uuid = uuid.UUID(job_id)

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid job ID",
        )

    db: Session = SessionLocal()

    try:
        job = db.get(
            Job,
            job_uuid,
        )

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found",
            )

        detections = (
            db.query(Detection)
            .filter(
                Detection.job_id == job_uuid
            )
            .all()
        )

        detection_data = []

        for detection in detections:

            detection_data.append(
                {
                    "id": detection.id,
                    "class_id": detection.class_id,
                    "class_name": detection.class_name,
                    "confidence": detection.confidence,
                    "bounding_box": {
                        "x1": detection.x1,
                        "y1": detection.y1,
                        "x2": detection.x2,
                        "y2": detection.y2,
                    },
                }
            )

        # PostgreSQL is the source of truth.
        result_image = None

        if job.result_object_key:
            result_image = (
                f"/result/{job.job_id}"
            )

        return {
            "job_id": str(job.job_id),
            "filename": job.filename,
            "status": job.status,
            "model": job.model,
            "created_at": (
                job.created_at.isoformat()
                if job.created_at
                else None
            ),
            "completed_at": (
                job.completed_at.isoformat()
                if job.completed_at
                else None
            ),
            "result_object_key": job.result_object_key,
            "result_image": result_image,
            "detections": detection_data,
            "detection_count": len(detection_data),
        }

    finally:
        db.close()


# --------------------------------------------------
# Get result image
# --------------------------------------------------

@app.get("/result/{job_id}")
def get_result(job_id: str):

    try:
        job_uuid = uuid.UUID(job_id)

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid job ID",
        )

    db: Session = SessionLocal()

    try:
        job = db.get(
            Job,
            job_uuid,
        )

        if not job:
            raise HTTPException(
                status_code=404,
                detail="Job not found",
            )

        # PostgreSQL is the source of truth.
        object_key = job.result_object_key

    finally:
        db.close()

    if not object_key:
        raise HTTPException(
            status_code=404,
            detail="Result not ready",
        )

    try:
        response = get_object(
            object_key
        )

    except Exception:
        raise HTTPException(
            status_code=404,
            detail="Result object not found",
        )

    return StreamingResponse(
        response["Body"].iter_chunks(
            chunk_size=1024 * 1024
        ),
        media_type="image/jpeg",
    )
