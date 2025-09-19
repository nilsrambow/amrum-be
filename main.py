import asyncio
from contextlib import asynccontextmanager
from collections import defaultdict
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import booking_router, guest_router, admin_router, alert_router, guest_booking_router
from app.config.config import get_rate_limit_config
from app.services.scheduler_service import scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting scheduler service...")
    scheduler_task = asyncio.create_task(scheduler_service.start_scheduler())

    yield

    # Shutdown
    print("Stopping scheduler service...")
    scheduler_service.stop_scheduler()
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass


app = FastAPI(lifespan=lifespan)

# Get rate limit configuration
rate_config = get_rate_limit_config()

# Add global rate limiting middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*", "https://127.0.0.1:8080", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory rate limiting
request_counts = defaultdict(list)

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Get client IP
    client_ip = request.client.host
    
    # Get current time
    now = datetime.now()
    
    # Clean old requests (older than 1 minute)
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] 
        if now - req_time < timedelta(minutes=1)
    ]
    
    # Check if limit exceeded
    if len(request_counts[client_ip]) >= rate_config["requests_per_minute"]:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"}
        )
    
    # Add current request
    request_counts[client_ip].append(now)
    
    # Process request
    response = await call_next(request)
    return response
app.include_router(booking_router.router)
app.include_router(guest_router.router)
app.include_router(admin_router.router)
app.include_router(alert_router.router)
app.include_router(guest_booking_router.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
