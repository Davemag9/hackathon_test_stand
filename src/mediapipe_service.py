import math
import cv2
import mediapipe as mp
import numpy as np

mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

VERTICAL_ROT_ANGLE_THRESHOLD = 20  # degrees

# --- Configuration ---
EAR_THRESHOLD = 0.25  # Threshold below which the eye is considered closed

# MediaPipe landmark indices for the Left Eye (P1 to P6)
LEFT_EYE_IDXS = [33, 160, 158, 133, 144, 153]
RIGHT_EYE_IDXS = [263, 387, 385, 362, 380, 373]

TOP_CENTER_POINT_IDX = 10
BOTTOM_CENTER_POINT_IDX = 152

# Define criteria for a uniform ID photo background
# A low standard deviation means consistent color
CONSISTENCY_THRESHOLD_STD = 30
# Average color should generally be bright (e.g., L > 200 in BGR scale where 255 is white)
BRIGHTNESS_THRESHOLD_MEAN = 255/2


def get_face_landmarks(bgr_image):
    # Convert the BGR image to RGB before processing, as MediaPipe expects RGB
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

    # 2. Initialize the Face Mesh processor
    # Static mode is often better for single images/inference
    with mp_face_mesh.FaceMesh(
            static_image_mode=True,
            max_num_faces=1,
            refine_landmarks=True,  # Optional: enables 478 landmarks for higher fidelity
            min_detection_confidence=0.5
    ) as face_mesh:
        # 3. Process the image
        # The image must be passed as a NumPy array in RGB format.
        results = face_mesh.process(rgb_image)

        # 4. Draw landmarks on the original BGR image
        # Create a copy to draw on
        annotated_image = bgr_image.copy()

        face_landmarks = None

        if results.multi_face_landmarks:
            face_landmarks = results.multi_face_landmarks[0]

        return face_landmarks


def draw_landmarks(image, face_landmarks):
    # Draw the connections (mesh) and the points
    mp_drawing.draw_landmarks(
        image=image,
        landmark_list=face_landmarks,
        connections=mp_face_mesh.FACEMESH_TESSELATION,  # Draws the full mesh
        landmark_drawing_spec=None,
        connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_tesselation_style())

    # Draw the contours (eyes, lips, etc.)
    mp_drawing.draw_landmarks(
        image=image,
        landmark_list=face_landmarks,
        connections=mp_face_mesh.FACEMESH_CONTOURS,  # Draws key facial features
        landmark_drawing_spec=None,
        connection_drawing_spec=mp_drawing_styles.get_default_face_mesh_contours_style())

    # 5. Display the result
    # Resize for better viewing if the image is large
    annotated_image = cv2.resize(image,
                                 (600, int(image.shape[0] * 600 / image.shape[1])))

    cv2.imshow("annotated_image", annotated_image)
    cv2.waitKey(0)  # Wait indefinitely for a key press
    cv2.destroyAllWindows()


def get_center_point(landmarks, H, W):
    # --- 2. Find the Min/Max Bounds (Bounding Box Edges) ---

    # Initialize min/max values for normalized coordinates (0.0 to 1.0)
    min_x = 1.0
    max_x = 0.0
    min_y = 1.0
    max_y = 0.0

    for lm in landmarks.landmark:
        # Update bounds using all 478 points
        min_x = min(min_x, lm.x)
        max_x = max(max_x, lm.x)
        min_y = min(min_y, lm.y)
        max_y = max(max_y, lm.y)

    # --- 3. Calculate the Geometric Center (Normalized) ---

    center_x_norm = (min_x + max_x) / 2
    center_y_norm = (min_y + max_y) / 2

    # --- 4. Convert to Pixel Coordinates and Draw ---

    center_x_pixel = int(center_x_norm * W)
    center_y_pixel = int(center_y_norm * H)

    center_point = (center_x_pixel, center_y_pixel)
    return center_point


def get_tip_of_nose(landmarks, H, W):
    lm = landmarks.landmark[4]  # Tip of the nose is landmark 1
    tip_x = int(lm.x * W)
    tip_y = int(lm.y * H)
    return (tip_x, tip_y)


def check_iris_centered(landmarks, eye_idxs, image, draw_contours=False):
    """
    Checks if the iris is centered within the eye region.
    """
    H, W, _ = image.shape

    # Extract the 6 required points in pixel coordinates
    eye_points_pixel = []
    for idx in eye_idxs:
        lm = landmarks.landmark[idx]
        pixel_x = int(lm.x * W)
        pixel_y = int(lm.y * H)
        eye_points_pixel.append((pixel_x, pixel_y))

    # Calculate the bounding box of the eye
    x_coords = [pt[0] for pt in eye_points_pixel]
    y_coords = [pt[1] for pt in eye_points_pixel]
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)

    # Get the iris center (landmark 468 for left eye, 473 for right eye)
    iris_idx = 468 if eye_idxs == LEFT_EYE_IDXS else 473
    iris_lm = landmarks.landmark[iris_idx]
    iris_x = int(iris_lm.x * W)
    iris_y = int(iris_lm.y * H)

    # Check if the iris is within the center region of the eye
    center_x = (min_x + max_x) // 2
    center_y = (min_y + max_y) // 2
    tolerance_x = (max_x - min_x) * 0.25
    tolerance_y = (max_y - min_y) * 0.25

    is_centered = (
            (abs(iris_x - center_x) <= tolerance_x)
            and (abs(iris_y - center_y) <= tolerance_y))

    if draw_contours:
        # Draw the eye bounding box
        cv2.rectangle(image, (min_x, min_y), (max_x, max_y), (255, 255, 0), 1)

        # Draw the iris position
        cv2.circle(image, (iris_x, iris_y), 2, (0, 255, 255), -1)

        # Draw the center region
        cv2.circle(image, (center_x, center_y), int(tolerance_x), (0, 255, 0), 1)

    return is_centered


def check_eyes_centered(landmarks, img):
    left_centered = check_iris_centered(landmarks, LEFT_EYE_IDXS, img, draw_contours=False)
    right_centered = check_iris_centered(landmarks, RIGHT_EYE_IDXS, img, draw_contours=False)
    return left_centered and right_centered


def euclidean_distance(point1, point2):
    """Calculates the 2D Euclidean distance between two points (x, y)."""
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)


def calculate_ear(eye_points):
    """
    Calculates the Eye Aspect Ratio (EAR) given 6 eye landmark points.
    Input points should be (x, y) pixel coordinates.
    """
    # Vertical distances (P2-P6 and P3-P5)
    A = euclidean_distance(eye_points[1], eye_points[5])
    B = euclidean_distance(eye_points[2], eye_points[4])

    # Horizontal distance (P1-P4)
    C = euclidean_distance(eye_points[0], eye_points[3])

    # EAR calculation
    ear = (A + B) / (2.0 * C)
    return ear


def check_eye_status(landmarks, eye_idxs, image, draw_contours=False):
    """Processes landmarks, calculates EAR, and returns status."""
    H, W, _ = image.shape

    # Extract the 6 required points in pixel coordinates
    eye_points_pixel = []
    for idx in eye_idxs:
        lm = landmarks.landmark[idx]
        pixel_x = int(lm.x * W)
        pixel_y = int(lm.y * H)
        eye_points_pixel.append((pixel_x, pixel_y))

    # Calculate EAR
    ear = calculate_ear(eye_points_pixel)

    # Determine status
    if ear < EAR_THRESHOLD:
        status = False
        color = (0, 0, 255)  # Red
    else:
        status = True
        color = (0, 255, 0)  # Green

    if draw_contours:
        # Display EAR and status near the eye (using one of the eye points for positioning)
        text = f"EAR: {ear:.2f} ({status})"
        cv2.putText(image, text, (eye_points_pixel[0][0], eye_points_pixel[0][1] - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        # Draw the eye contour for visualization
        # We can use numpy to reshape and draw polylines
        points_array = np.array(eye_points_pixel, dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(image, [points_array], isClosed=True, color=color, thickness=1)

    return status, ear


def check_eyes_open(landmarks, img):
    left_status, left_ear = check_eye_status(landmarks, LEFT_EYE_IDXS, img)
    right_status, right_ear = check_eye_status(landmarks, RIGHT_EYE_IDXS, img)

    # print(f"Left Eye Status: {left_status}, EAR: {left_ear:.4f}")
    # print(f"Right Eye Status: {right_status}, EAR: {right_ear:.4f}")

    return left_status and right_status, min(left_ear, right_ear)


def get_vertical_centerline(landmarks, img):
    H, W, _ = img.shape
    landmarks = landmarks.landmark

    def get_pixel_coords(idx):
        lm = landmarks[idx]
        return (int(lm.x * W), int(lm.y * H))

    pA = get_pixel_coords(TOP_CENTER_POINT_IDX)  # (x, y) for point 10
    pB = get_pixel_coords(BOTTOM_CENTER_POINT_IDX)  # (x, y) for point 152

    # print(f"Point A ({IDX_A}) coords: {pA}")
    # print(f"Point B ({IDX_B}) coords: {pB}")

    vertical_shift = pA[1] - pB[1]
    horizontal_shift = pA[0] - pB[0]
    if vertical_shift == 0:
        tan = 1e10
    else:
        tan = abs(horizontal_shift) / (abs(vertical_shift) + 1e-10)
    angle = math.degrees(math.atan(tan))
    # print(f"Angle: {angle}")
    return angle, pA, pB


def check_vertical_rotation(landmarks, img):
    angle, pA, pB = get_vertical_centerline(landmarks, img)
    return angle <= VERTICAL_ROT_ANGLE_THRESHOLD, angle


# background consistent color detection

    # Initialize MediaPipe Selfie Segmentation
mp_selfie_segmentation = mp.solutions.selfie_segmentation
segmentation = mp_selfie_segmentation.SelfieSegmentation(model_selection=1)


def extract_background(bgr_image, threshold=0.1):
    image_rgb = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

    # Process the image and get the segmentation mask
    results = segmentation.process(image_rgb)
    mask = results.segmentation_mask

    background_mask = (mask < threshold) # Boolean mask: True for background, False for person
    background_pixels = bgr_image[background_mask]
    return background_pixels, mask


def is_background_consistent(image):
    background_pixels, mask = extract_background(image)

    mean_color = np.mean(background_pixels, axis=0)
    std_dev_color = np.std(background_pixels, axis=0)
    max_std_dev = np.max(std_dev_color)


    is_consistent = max_std_dev < CONSISTENCY_THRESHOLD_STD
    is_bright_enough = np.mean(mean_color) > BRIGHTNESS_THRESHOLD_MEAN
    return is_consistent, is_bright_enough