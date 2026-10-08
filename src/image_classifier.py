"""Image classification providers used by the recovery API."""

import os


DEFAULT_THRESHOLD = 0.80


def classify_with_rekognition(image_bytes: bytes, model_arn: str | None = None, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Classify one image with a running Rekognition Custom Labels model."""
    import boto3

    model_arn = model_arn or os.environ["REKOGNITION_MODEL_ARN"]
    region = os.getenv("AWS_REGION", "ap-south-1")
    client = boto3.client("rekognition", region_name=region)
    response = client.detect_custom_labels(ProjectVersionArn=model_arn, Image={"Bytes": image_bytes})

    detections = []
    for label in response.get("CustomLabels", []):
        name = label.get("Name", "other").lower()
        confidence = round(float(label.get("Confidence", 0)) / 100, 4)
        material = "pet" if name in {"pet", "plastic", "plastic bottle"} else name
        if material not in {"pet", "cardboard", "paper", "aluminium", "glass"}:
            material = "other"
        detections.append(
            {
                "materialType": material,
                "confidence": confidence,
                "requiresConfirmation": confidence < threshold or material == "other",
            }
        )

    detections.sort(key=lambda item: item["confidence"], reverse=True)
    return {"detections": detections, "mode": "aws"}


def classify_s3_object(bucket: str, key: str, model_arn: str | None = None, threshold: float = DEFAULT_THRESHOLD) -> dict:
    """Classify an image already uploaded to a private S3 object."""
    import boto3

    model_arn = model_arn or os.environ["REKOGNITION_MODEL_ARN"]
    region = os.getenv("AWS_REGION", "ap-south-1")
    client = boto3.client("rekognition", region_name=region)
    response = client.detect_custom_labels(ProjectVersionArn=model_arn, Image={"S3Object": {"Bucket": bucket, "Name": key}})
    return _normalize_custom_labels(response.get("CustomLabels", []), threshold)


def _normalize_custom_labels(labels: list[dict], threshold: float) -> dict:
    detections = []
    for label in labels:
        name = label.get("Name", "other").lower()
        confidence = round(float(label.get("Confidence", 0)) / 100, 4)
        material = "pet" if name in {"pet", "plastic", "plastic bottle"} else name
        if material not in {"pet", "cardboard", "paper", "aluminium", "glass"}:
            material = "other"
        detections.append({"materialType": material, "confidence": confidence, "requiresConfirmation": confidence < threshold or material == "other"})
    detections.sort(key=lambda item: item["confidence"], reverse=True)
    return {"detections": detections, "mode": "aws"}
