from ultralytics import YOLO
from PIL import Image


class CVDetector:
    def __init__(self, model_path="yolo11n.pt"):
        self.model = YOLO(model_path)

    def predict(self, image_path: str):
        image = Image.open(image_path).convert("RGB")

        results = self.model(image)
        result = results[0]

        detections = []

        for box in result.boxes:
            class_id = int(box.cls[0])
            confidence = float(box.conf[0])

            x1, y1, x2, y2 = box.xyxy[0].tolist()

            detections.append({
                "class_id": class_id,
                "class_name": self.model.names[class_id],
                "confidence": round(confidence, 4),
                "bounding_box": {
                    "x1": round(x1, 2),
                    "y1": round(y1, 2),
                    "x2": round(x2, 2),
                    "y2": round(y2, 2)
                }
            })

        annotated = result.plot()

        return detections, annotated
