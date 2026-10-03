from app.detector import CVDetector

if __name__ == "__main__":
    detector = CVDetector()

    print("CV Worker initialized successfully.")
    print("Model:", detector.model.ckpt_path)
