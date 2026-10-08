# Image Classification / Detection Setup

This directory defines the optional image-assisted material identification
feature. Manual material entry remains the primary path.

## Initial labels

Use these controlled labels:

```text
pet
cardboard
paper
aluminium
glass
```

Do not train `wood` or `other/unknown` in the first model. They should remain
manual-selection outcomes until we have enough representative images.

## Dataset layout

Keep downloaded images outside Git:

```text
ml/data/
├── training/
│   ├── pet/
│   ├── cardboard/
│   ├── paper/
│   ├── aluminium/
│   └── glass/
└── testing/
    ├── pet/
    ├── cardboard/
    ├── paper/
    ├── aluminium/
    └── glass/
```

For object detection, each image must also have annotations identifying the
object location. For image-level classification, the folder/class label is
enough. We should prefer object detection when images may contain multiple
items; otherwise begin with classification for the faster proof of concept.

## Labeling rules

- Label the material visible in the image, not the intended disposal category.
- Use one label only when the image clearly contains one dominant item.
- Do not label ambiguous, heavily occluded, or unreadable objects as a precise
  material; move them to a review queue.
- Include variation in lighting, angle, background, cleanliness, and object
  condition.
- Avoid near-duplicate images across training and testing.
- Keep test images separate and unseen during training.

## Recommended first dataset

Use TrashNet for an initial controlled baseline, then add a small curated set
of realistic household images. TACO can help add “waste in context” variation,
but its categories may need mapping to our narrower labels.

Target at least 50–100 usable images per class for the first useful prototype,
with a separate test set. If time is limited, use fewer images but report the
model as a proof of concept rather than a general waste detector.

## Preparing local data

After downloading a dataset such as TrashNet outside Git, run:

```bash
python3 scripts/prepare_dataset.py /path/to/trashnet/data/dataset-resized
```

The script maps `plastic` to `pet` and `metal` to `aluminium`, skips unmapped
classes such as `trash`, and creates deterministic `ml/data/training/` and
`ml/data/testing/` folders. Add curated and TACO images only after reviewing
their labels and licenses.

Audit a prepared dataset before uploading it to S3:

```bash
python3 scripts/audit_dataset.py /tmp/trashnet-prepared
```

The audit checks expected labels, per-split counts, and filename overlap between
training and testing data.

For TACO, retain the COCO bounding-box annotations and use:

```bash
python3 scripts/prepare_taco_dataset.py \
  /path/to/TACO/data/annotations.json \
  /path/to/TACO/data \
  --output /tmp/taco-prepared
```

The adapter maps selected TACO categories into our five labels and skips
categories that are not appropriate for the first model. Review the mapping in
`scripts/prepare_taco_dataset.py` before using the output for training.

## Model behavior

The backend should normalize inference to:

```json
{
  "detections": [
    {
      "materialType": "pet",
      "confidence": 0.92,
      "requiresConfirmation": false
    }
  ],
  "mode": "mock"
}
```

Low-confidence, multi-label, or unknown results must require user confirmation.
The model never determines quantity; weight remains user-entered.

## AWS path

1. Create a Rekognition Custom Labels project.
2. Upload separate training and testing datasets from S3.
3. Train and inspect per-label performance.
4. Start the model only when inference is needed.
5. Call `DetectCustomLabels` from the backend.
6. Normalize labels and confidence into the response above.
7. Ask the user to confirm/correct the material.
8. Delete the temporary source image and stop the model when finished.

Never commit image datasets, credentials, model ARNs, or uploaded household
photos to this repository.
