import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from app.api.routes import booking_router, guest_router, admin_router, alert_router, guest_booking_router
from app.config.config import get_rate_limit_config
from app.services.scheduler_service import scheduler_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting scheduler service...")
    scheduler_task = asyncio.create_task(scheduler_service.start_scheduler())
    
    # Initialize rate limiter (using in-memory storage for simplicity)
    await FastAPILimiter.init()

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

# Add global rate limiting dependency
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    # Apply rate limiting to all requests
    rate_limiter = RateLimiter(
        times=rate_config["requests_per_minute"], 
        seconds=60
    )
    await rate_limiter(request)
    response = await call_next(request)
    return response
app.include_router(booking_router.router)
app.include_router(guest_router.router)
app.include_router(admin_router.router)
app.include_router(alert_router.router)
app.include_router(guest_booking_router.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
