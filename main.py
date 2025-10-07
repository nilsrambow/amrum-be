import asyncio
from contextlib import asynccontextmanager
from collections import defaultdict
from datetime import datetime, timedelta

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import booking_router, guest_router, admin_router, alert_router, guest_booking_router, auth_router
from app.config.config import get_rate_limit_config, get_cors_config
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

# Get configurations
rate_config = get_rate_limit_config()
cors_config = get_cors_config()

# Add CORS middleware - restrict to allowed frontends only
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_config["allow_origins"],
    allow_credentials=cors_config["allow_credentials"],
    allow_methods=cors_config["allow_methods"],
    allow_headers=cors_config["allow_headers"],
)

# Improved in-memory rate limiting
request_counts = defaultdict(list)
last_cleanup = datetime.now()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    global last_cleanup
    
    # Get client IP
    client_ip = request.client.host
    
    # Get current time
    now = datetime.now()
    
    # Periodic cleanup to avoid memory bloat (every 5 minutes)
    if now - last_cleanup > timedelta(minutes=5):
        # Clean up old IPs that haven't been used recently
        cutoff_time = now - timedelta(hours=1)
        for ip in list(request_counts.keys()):
            request_counts[ip] = [
                req_time for req_time in request_counts[ip] 
                if req_time > cutoff_time
            ]
            if not request_counts[ip]:
                del request_counts[ip]
        last_cleanup = now
    
    # Clean old requests for this IP (older than 1 minute)
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] 
        if now - req_time < timedelta(minutes=1)
    ]
    
    # Check if limit would be exceeded
    if len(request_counts[client_ip]) >= rate_config["requests_per_minute"]:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content={
                "detail": f"Rate limit exceeded. Max {rate_config['requests_per_minute']} requests per minute.",
                "current_count": len(request_counts[client_ip]),
                "limit": rate_config["requests_per_minute"]
            }
        )
    
    # Add current request
    request_counts[client_ip].append(now)
    
    # Process request
    response = await call_next(request)
    return response
# Debug endpoint to check rate limiting status
@app.get("/debug/rate-limit-status")
async def get_rate_limit_status(request: Request):
    client_ip = request.client.host
    now = datetime.now()
    
    # Clean old requests for this IP
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip] 
        if now - req_time < timedelta(minutes=1)
    ]
    
    return {
        "client_ip": client_ip,
        "current_requests": len(request_counts[client_ip]),
        "limit": rate_config["requests_per_minute"],
        "remaining": rate_config["requests_per_minute"] - len(request_counts[client_ip]),
        "reset_time": "1 minute from oldest request" if request_counts[client_ip] else "immediately",
        "total_tracked_ips": len(request_counts),
        "debug_info": {
            "rate_config": rate_config,
            "env_var_requests_per_minute": os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "NOT_SET"),
            "env_var_burst": os.getenv("RATE_LIMIT_BURST", "NOT_SET"),
            "env_var_env": os.getenv("ENV", "NOT_SET")
        }
    }

app.include_router(booking_router.router)
app.include_router(guest_router.router)
app.include_router(admin_router.router)
app.include_router(alert_router.router)
app.include_router(guest_booking_router.router)
app.include_router(auth_router.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
