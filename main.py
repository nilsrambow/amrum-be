import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import booking_router, guest_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://127.0.0.1:8080", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(booking_router.router)
app.include_router(guest_router.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=True)

