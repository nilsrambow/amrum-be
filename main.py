import asyncio
from contextlib import asynccontextmanager
from collections import defaultdict
from datetime import datetime, timedelta
import json

import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes import booking_router, guest_router, admin_router, alert_router, guest_booking_router, auth_router, dashboard_router
from app.config.config import get_rate_limit_config, get_cors_config
from app.services.scheduler_service import scheduler_service

# region agent log helpers
_AGENT_DEBUG_LOG_PATH = "/Users/nils/coding/amrum-be/.cursor/debug.log"


def _agent_log(*, hypothesisId: str, location: str, message: str, data: dict):
    # Never log secrets (passwords/tokens/PII). Keep payload small.
    try:
        payload = {
            "sessionId": "debug-session",
            "runId": "pre-fix",
            "hypothesisId": hypothesisId,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(datetime.now().timestamp() * 1000),
        }
        with open(_AGENT_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        # Avoid breaking request handling due to logging failures.
        pass
# endregion


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

# region agent log - exception handlers
@app.exception_handler(RequestValidationError)
async def _agent_request_validation_handler(request: Request, exc: RequestValidationError):
    if request.url.path == "/auth/login":
        # region agent log
        _agent_log(
            hypothesisId="B",
            location="main.py:request_validation_handler",
            message="Request validation failed",
            data={
                "path": request.url.path,
                "method": request.method,
                "errors_count": len(exc.errors()),
                "errors": exc.errors()[:5],
            },
        )
        # endregion
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(StarletteHTTPException)
async def _agent_starlette_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path == "/auth/login" and exc.status_code in (400, 401, 403, 404, 415):
        # region agent log
        _agent_log(
            hypothesisId="C",
            location="main.py:starlette_http_exception_handler",
            message="HTTPException on /auth/login",
            data={
                "path": request.url.path,
                "method": request.method,
                "status_code": exc.status_code,
                "detail": getattr(exc, "detail", None),
            },
        )
        # endregion
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
# endregion

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
    
    # region agent log - login request probe (runs before route parsing)
    if request.url.path == "/auth/login":
        safe_headers = {}
        for k in ("content-type", "origin", "host", "user-agent", "referer"):
            v = request.headers.get(k)
            if v:
                safe_headers[k] = v

        # region agent log
        _agent_log(
            hypothesisId="A",
            location="main.py:login_probe:enter",
            message="Incoming /auth/login request",
            data={
                "method": request.method,
                "path": request.url.path,
                "headers": safe_headers,
            },
        )
        # endregion

        body_bytes = b""
        body_keys = None
        body_json_ok = None
        username_len = None
        username_has_at = None
        password_len = None
        try:
            body_bytes = await request.body()
            try:
                body_obj = json.loads(body_bytes.decode("utf-8")) if body_bytes else None
                body_json_ok = isinstance(body_obj, dict)
                if isinstance(body_obj, dict):
                    body_keys = sorted(list(body_obj.keys()))[:20]
                    u = body_obj.get("username")
                    p = body_obj.get("password")
                    if isinstance(u, str):
                        username_len = len(u)
                        username_has_at = ("@" in u)
                    if isinstance(p, str):
                        password_len = len(p)
            except Exception:
                body_json_ok = False
        except Exception:
            body_json_ok = None

        # region agent log
        _agent_log(
            hypothesisId="B",
            location="main.py:login_probe:body",
            message="Parsed /auth/login body metadata",
            data={
                "content_length": len(body_bytes) if body_bytes is not None else None,
                "body_json_ok": body_json_ok,
                "body_keys": body_keys,
                "username_len": username_len,
                "username_has_at": username_has_at,
                "password_len": password_len,
            },
        )
        # endregion
    # endregion

    # Process request
    response = await call_next(request)

    if request.url.path == "/auth/login":
        # region agent log
        _agent_log(
            hypothesisId="A",
            location="main.py:login_probe:exit",
            message="Completed /auth/login request",
            data={"status_code": getattr(response, "status_code", None)},
        )
        # endregion

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
        "total_tracked_ips": len(request_counts)
    }

app.include_router(booking_router.router)
app.include_router(guest_router.router)
app.include_router(admin_router.router)
app.include_router(alert_router.router)
app.include_router(guest_booking_router.router)
app.include_router(auth_router.router)
app.include_router(dashboard_router.router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
