import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.router import classify_photo_router
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["accept", "Content-Type"],
)

@app.get ("/")
async def health_check():
    return {"status": "ok"}
app.include_router(classify_photo_router, prefix="/api", tags=["Classify Photo"])

if __name__ == '__main__':
    uvicorn.run(
        "app:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        ssl_keyfile="front for hackathon/key.pem",
        ssl_certfile="front for hackathon/cert.pem"
    )
