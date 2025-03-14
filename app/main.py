from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import booking, guest

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://127.0.0.1:8080", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(booking.router)
app.include_router(guest.router)


@app.get("/")
def read_root():
    return {"mesage": "Welcome to Amrum Manager!"}
