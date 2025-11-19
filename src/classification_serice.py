import cv2

from src.mediapipe_service import get_face_landmarks, draw_landmarks, get_center_point, get_tip_of_nose


def classify_image(img):
    # Dummy implementation for image classification
    # In a real scenario, this function would use a machine learning model to classify the image
    landmarks = get_face_landmarks(img)
    if landmarks is None:
        return {"label": "no_face_detected", "confidence": 0.0}
    else:
        geo_center_point = get_center_point(landmarks, img.shape[0], img.shape[1])
        tip_of_nose_point = get_tip_of_nose(landmarks, img.shape[0], img.shape[1])

        cv2.circle(img, geo_center_point, 7, (0, 0, 255), -1)
        cv2.circle(img, tip_of_nose_point, 6, (0, 255, 0), -1)

        draw_landmarks(img, landmarks)
        return {"label": "cat", "confidence": 0.98}