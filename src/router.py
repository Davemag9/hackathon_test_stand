from fastapi import APIRouter, UploadFile, File, HTTPException
from src.classification_serice import classify_image, classify_glasses
from src.utils import image_bytes_to_cv2

classify_photo_router = APIRouter()

@classify_photo_router.post("/classify")
async def classify_photo(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Invalid image format")

    # Read file bytes
    image_bytes = await file.read()
    cv_image = image_bytes_to_cv2(image_bytes)

    result = classify_image(cv_image)

    glasses_result = classify_glasses(cv_image)

    is_glasses = glasses_result == "anyglasses"

    return {
        "no_glasses": not is_glasses, 
        "is_centered": result["is_centered"], 
        "open_eye_status": result["open_eye_status"], 
        "is_vertical_straight": result["is_vertical_straight"]
    }
