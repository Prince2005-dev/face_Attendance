import logging
logging.getLogger("deepface").setLevel(logging.ERROR)

from deepface import DeepFace
import os
from config import DATASET_PATH, CONFIDENCE_THRESHOLD

def recognize_face(frame):
    try:
        results = DeepFace.find(
            img_path=frame,
            db_path=DATASET_PATH,
            model_name="Facenet",
            enforce_detection=False
        )

        if results and len(results[0]) > 0:
            best = results[0].iloc[0]

            distance = best["distance"]
            identity = best["identity"]

            # DEBUG (optional, remove later)
            print(f"[DEBUG] distance: {distance:.4f}")

            if distance < CONFIDENCE_THRESHOLD:
                name = os.path.basename(os.path.dirname(identity))
                return name, distance

        return "Unknown", None

    except Exception as e:
        print(f"[ERROR] Recognition failed: {e}")
        return "Unknown", None