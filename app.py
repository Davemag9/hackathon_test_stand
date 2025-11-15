import uvicorn

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.router import classify_photo_router
app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost",
    "http://93.115.23.34/",
    "http://93.115.23.34:80",
    "https://93.115.23.34:80",
    "https://xtayl.com",
    "http://xtayl.com",
    "chrome-extension://*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get ("/")
async def health_check():
    return {"status": "ok"}
app.include_router(classify_photo_router, prefix="/api", tags=["Classify Photo"])

if __name__ == '__main__':
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
