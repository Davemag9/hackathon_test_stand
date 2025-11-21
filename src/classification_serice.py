import cv2
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

from .mediapipe_service import get_face_landmarks, draw_landmarks, get_center_point, get_tip_of_nose, \
    check_eyes_open, check_vertical_rotation


def check_face_centered(landmarks, img, tolerance_bbox=(20, 20)):
    geo_center_point = get_center_point(landmarks, img.shape[0], img.shape[1])
    tip_of_nose_point = get_tip_of_nose(landmarks, img.shape[0], img.shape[1])

    h_centered = abs(geo_center_point[0] - tip_of_nose_point[0]) <= tolerance_bbox[0]
    v_centered = abs(geo_center_point[1] - tip_of_nose_point[1]) <= tolerance_bbox[1]

    if h_centered and v_centered:
        return True
    else:
        return False


def classify_image(img):
    # Dummy implementation for image classification
    # In a real scenario, this function would use a machine learning model to classify the image
    landmarks = get_face_landmarks(img)
    if landmarks is None:
        return {"label": "no_face_detected", "confidence": 0.0}
    else:

        is_valid_photo = True

        # is centered check
        is_centered = check_face_centered(landmarks, img)
        is_valid_photo &= is_centered

        # open eyes check
        open_eye_status, min_ear_score = check_eyes_open(landmarks, img)
        is_valid_photo &= (open_eye_status == True)

        # rotation check
        is_vertical_straight = check_vertical_rotation(landmarks, img)
        is_valid_photo &= (is_vertical_straight == True)


        # ----- demo code, can be removed --------------------------------------------
        geo_center_point = get_center_point(landmarks, img.shape[0], img.shape[1])
        tip_of_nose_point = get_tip_of_nose(landmarks, img.shape[0], img.shape[1])

        cv2.circle(img, geo_center_point, 7, (0, 0, 255), -1)
        cv2.circle(img, tip_of_nose_point, 6, (0, 255, 0), -1)

        cv2.rectangle(
            img,
            (geo_center_point[0] - 10, geo_center_point[1] - 10),
            (geo_center_point[0] + 10, geo_center_point[1] + 10),
            (0, 0, 255), 2)
        draw_landmarks(img, landmarks)
        # ------------------------------------------------------------------------------


        print("centered:", is_centered)
        print("eyes open:", open_eye_status)
        print("not rotated:", is_vertical_straight)

        print("is valid:", is_valid_photo)

        return {"is_valid_photo": is_valid_photo, 'comment': "..."}


def classify_glasses(img):

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1)

    model.fc = nn.Sequential(
        nn.Dropout(0.5),
        nn.Linear(model.fc.in_features, 2)
    )

    # Load trained weights
    model.load_state_dict(torch.load("data/best_model.pth", map_location=device))

    model.to(device)
    model.eval()

    transform_eval = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor()
])

    # Convert cv2 image (numpy array, BGR) to PIL Image (RGB)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(img_rgb)
    x = transform_eval(img).unsqueeze(0).to(device)

    with torch.no_grad():
        out = model(x)
        pred = out.argmax(1).item()

    classes = ["anyglasses", "no_anyglasses"]
    return classes[pred]

