import os

import boto3
from botocore.client import Config


S3_ENDPOINT_URL = os.getenv(
    "S3_ENDPOINT_URL",
    "http://localhost:8333",
)

S3_ACCESS_KEY = os.getenv(
    "S3_ACCESS_KEY",
    "cloudai",
)

S3_SECRET_KEY = os.environ["S3_SECRET_KEY"]

S3_BUCKET = os.getenv(
    "S3_BUCKET",
    "cloud-ai-files",
)


s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    config=Config(signature_version="s3v4"),
    region_name="us-east-1",
)


def upload_file(
    local_path: str,
    object_key: str,
    content_type: str | None = None,
):
    extra_args = {}

    if content_type:
        extra_args["ContentType"] = content_type

    s3.upload_file(
        local_path,
        S3_BUCKET,
        object_key,
        ExtraArgs=extra_args,
    )


def download_file(
    object_key: str,
    local_path: str,
):
    s3.download_file(
        S3_BUCKET,
        object_key,
        local_path,
    )


def delete_file(object_key: str):
    s3.delete_object(
        Bucket=S3_BUCKET,
        Key=object_key,
    )


def object_exists(object_key: str) -> bool:
    try:
        s3.head_object(
            Bucket=S3_BUCKET,
            Key=object_key,
        )
        return True

    except s3.exceptions.ClientError:
        return False


def get_object(object_key: str):
    return s3.get_object(
        Bucket=S3_BUCKET,
        Key=object_key,
    )
