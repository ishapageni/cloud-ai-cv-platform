# Cloud AI CV Platform

A containerized computer vision inference platform for asynchronous image processing using YOLO, FastAPI, Redis, PostgreSQL, SeaweedFS, Docker, and Next.js.

## Overview

Cloud AI CV Platform allows users to upload images through a web dashboard and submit them for asynchronous computer vision inference.

The platform separates API handling from model inference using a Redis-backed job queue and a dedicated CV worker.

## System Architecture

The platform uses an asynchronous inference architecture with FastAPI, Redis, PostgreSQL, SeaweedFS, and a dedicated YOLO inference worker.

See the detailed [system architecture](docs/architecture.md).

### Key capabilities

- Image upload through a Next.js web interface
- YOLO object detection
- Asynchronous inference using Redis
- PostgreSQL job and detection persistence
- S3-compatible object storage with SeaweedFS
- Annotated detection results
- Job status tracking
- Detection confidence and bounding-box information
- Dockerized backend and worker services
- Persistent PostgreSQL and object-storage volumes

  
## Processing Pipeline

1. User uploads an image from the Next.js dashboard.
2. FastAPI temporarily stores the input.
3. The image is uploaded to SeaweedFS.
4. A job record is created in PostgreSQL.
5. A job message is pushed to Redis.
6. The CV worker consumes the job.
7. The worker downloads the image from SeaweedFS.
8. YOLO performs object detection.
9. Bounding boxes and confidence scores are extracted.
10. An annotated result image is generated.
11. The result is uploaded to SeaweedFS.
12. Detection metadata is persisted in PostgreSQL.
13. The frontend polls the job endpoint and displays the completed result.


## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, TypeScript |
| Backend | FastAPI, Python |
| Computer Vision | Ultralytics YOLO, OpenCV, Pillow |
| Database | PostgreSQL |
| Job Queue | Redis |
| Object Storage | SeaweedFS S3 API |
| Containerization | Docker, Docker Compose |
| API | REST |
|Model | YOLO11n |

## Project Structure
```
cloud-ai-cv-platform/
├── backend/
│   ├── app/
│   │   ├── db/
│   │   ├── services/
│   │   └── main.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── requirements-docker.txt
│
├── cv_worker/
│   └── app/
│       ├── detector.py
│       ├── redis_worker.py
│       └── worker.py
│
├── frontend/
│   └── src/
│       └── app/
│
├── seaweedfs/
│   └── s3.json.example
│
├── docker-compose.yml
├── .env.example
└── .gitignore
```
## Running Locally

### Prerequisites

* Docker Desktop
* Git
* Node.js

### 1. Clone the repositorygit clone 
```bash
git clone https://github.com/ishapageni/cloud-ai-cv-platform.git
cd cloud-ai-cv-platform
```
### 2. Configure environment variables

Create a local .env file from the example:
```bash
 cp .env.example .env
```
Update the values in .env as required.

The .env file is intentionally excluded from Git.

### 3. Configure SeaweedFS

Create the local S3 configuration:
```bash
cp seaweedfs/s3.json.example seaweedfs/s3.json
```
Update the local credentials if necessary.

seaweedfs/s3.json is excluded from Git.

### 4. Start the backend infrastructure
```bash
docker compose up -d
```
This starts:

* PostgreSQL
* Redis
* SeaweedFS
* FastAPI backend
* CV worker

### 5. Start the frontend
```bash
cd frontend
npm install
npm run dev
```
The dashboard will be available at:
```http://localhost:3000```

The FastAPI backend runs on:
```http://localhost:8000```

## API Endpoints

### Health Check
```http
GET /health
```
Checks whether the API is running.

### Submit Image
```http
POST /predict
```
Uploads an image and creates an asynchronous inference job.

### Get Job
```http
GET /jobs/{job_id}
```
Returns the current job status and detection information.

### List Jobs
```http
GET /jobs
```
Returns previously processed jobs.

### Get Result
```http
GET /result/{job_id}
```
Returns the annotated result image.

### Example Detection

```JSON
A completed job returns detection metadata containing:
{
  "class_id": 0,
  "class_name": "person",
  "confidence": 0.9231,
  "bounding_box": {
    "x1": 120.4,
    "y1": 85.2,
    "x2": 315.7,
    "y2": 462.1
  }
}
```

## Design Decisions

### Asynchronous inference

Model inference is separated from the API server using Redis.

This prevents long-running inference operations from blocking the request-handling layer and allows additional workers to be added later.

### Object storage

Input and output images are stored in SeaweedFS through its S3-compatible API rather than relying on the backend container filesystem.

### Persistent metadata

PostgreSQL stores job lifecycle information and individual detections, allowing the frontend to display inference history and structured detection statistics.

### Containerized services

The backend and CV worker use the same Docker image while running different processes.

This keeps the environment reproducible and makes the worker architecture easier to scale.

### Future Improvements

* Horizontal CV worker scaling
* Model registry
* Multiple computer vision models
* Video inference
* Image classification
* Semantic and instance segmentation
* OCR
* Authentication and authorization
* Rate limiting
* Observability and metrics
* GPU-enabled inference
* Kubernetes deployment
* Cloud deployment
* CI/CD pipeline

## Security

Secrets are provided through environment variables and local configuration files.

The following files are intentionally excluded from Git:
```
.env
seaweedfs/s3.json
```
Only example configuration files containing placeholder values are committed.

