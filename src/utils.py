import cv2
import numpy as np


def image_bytes_to_cv2(image_bytes: bytes, keep_alpha: bool = False) -> np.ndarray:
    """
    Convert raw image bytes to an OpenCV image (BGR by default).

    Args:
        image_bytes: Raw bytes of the image (e.g., await file.read()).
        keep_alpha: If True and image has alpha channel, return BGRA; otherwise convert to BGR.

    Returns:
        OpenCV image as a numpy array.

    Raises:
        ValueError: If image decoding fails.
    """
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_UNCHANGED)  # returns BGR or BGRA or grayscale
    if img is None:
        raise ValueError("Could not decode image bytes to an image")
    # If grayscale, convert to BGR for consistency
    if img.ndim == 2:
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    # Drop alpha if requested
    if not keep_alpha and img.ndim == 3 and img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
    return img