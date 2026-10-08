"""Private S3 upload helpers for temporary household images."""

import os
from uuid import uuid4


def create_upload(bucket: str, content_type: str, filename: str) -> dict:
    import boto3

    extension = ".jpg" if content_type == "image/jpeg" else ".png"
    key = f"demo-uploads/{uuid4().hex}{extension}"
    client = boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-south-1"))
    url = client.generate_presigned_url("put_object", Params={"Bucket": bucket, "Key": key, "ContentType": content_type, "ServerSideEncryption": "AES256"}, ExpiresIn=600)
    return {"uploadUrl": url, "key": key, "expiresIn": 600}


def delete_upload(bucket: str, key: str) -> None:
    import boto3

    boto3.client("s3", region_name=os.getenv("AWS_REGION", "ap-south-1")).delete_object(Bucket=bucket, Key=key)
