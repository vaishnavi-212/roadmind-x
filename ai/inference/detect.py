from ultralytics import YOLO
from ai.inference.preprocess import preprocess
import numpy as np
from typing import List, dict
import os

# Hazard classes the model detects
HAZARD_CLASSES = {
    0: "pothole",
    1: "flood",
    2: "debris",
    3: "construction",
    4: "accident",
    5: "speed_bump"
}

# Severity mapping based on confidence score
def get_severity(confidence: float) -> str:
    if confidence >= 0.75:
        return "high"
    elif confidence >= 0.5:
        return "medium"
    else:
        return "low"


class RoadHazardDetector:
    def __init__(self, model_path: str, confidence_threshold: float = 0.5):
        self.confidence_threshold = confidence_threshold
        
        # Load model if weights exist, else use pretrained yolov8n
        if os.path.exists(model_path):
            self.model = YOLO(model_path)
        else:
            print(f"[WARN] Model not found at {model_path}, loading yolov8n base")
            self.model = YOLO("yolov8n.pt")

    def detect(self, image_input) -> List[dict]:
        """
        Run detection on a single image.
        Returns list of detected hazards with type, confidence, severity.
        """
        image = preprocess(image_input)

        # YOLO expects 0-255 uint8, convert back
        image_uint8 = (image * 255).astype(np.uint8)

        results = self.model(image_uint8, verbose=False)
        detections = []

        for result in results:
            for box in result.boxes:
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])

                if confidence < self.confidence_threshold:
                    continue

                hazard_type = HAZARD_CLASSES.get(class_id, "unknown")
                severity = get_severity(confidence)

                # Bounding box coords (normalized)
                x1, y1, x2, y2 = box.xyxyn[0].tolist()

                detections.append({
                    "hazard_type": hazard_type,
                    "confidence": round(confidence, 3),
                    "severity": severity,
                    "bbox": {
                        "x1": round(x1, 3),
                        "y1": round(y1, 3),
                        "x2": round(x2, 3),
                        "y2": round(y2, 3)
                    }
                })

        return detections


    def detect_batch(self, images: list) -> List[List[dict]]:
        """
        Run detection on a batch of images.
        Returns list of detection lists.
        """
        return [self.detect(img) for img in images]