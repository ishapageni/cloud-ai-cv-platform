FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    && rm -rf /var/lib/apt/lists/*FROM python:3.14-slim

COPY backend/requirements-docker.txt /app/requirements-docker.txt

RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.14.1 \
    torchvision==0.29.1

RUN pip install --no-cache-dir \
    -r /app/requirements-docker.txt

COPY backend /app/backend
COPY cv_worker /app/cv_worker

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
