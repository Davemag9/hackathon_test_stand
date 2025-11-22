import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.router import classify_photo_router
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST"],
    allow_headers=["accept", "Content-Type"],
)

@app.get ("/")
async def health_check():
    return {"status": "ok"}
app.include_router(classify_photo_router, prefix="/api", tags=["Classify Photo"])

if __name__ == '__main__':
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
