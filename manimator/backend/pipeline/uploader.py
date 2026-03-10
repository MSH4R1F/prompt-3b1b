import os

import boto3


def upload_to_r2(video_path: str, job_id: str) -> str:
    """Upload a .mp4 file to Cloudflare R2 and return the public URL."""
    client = boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["R2_ACCESS_KEY"],
        aws_secret_access_key=os.environ["R2_SECRET_KEY"],
    )

    bucket = os.environ["R2_BUCKET"]
    key = f"videos/{job_id}.mp4"

    with open(video_path, "rb") as file_obj:
        client.put_object(Bucket=bucket, Key=key, Body=file_obj, ContentType="video/mp4")

    public_url = os.environ["R2_PUBLIC_URL"].rstrip("/")  # guard against double-slash
    return f"{public_url}/{key}"
