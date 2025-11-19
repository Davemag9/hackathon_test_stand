import cv2
import mediapipe as mp


mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles



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