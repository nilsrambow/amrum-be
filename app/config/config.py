import os
import logging

from dotenv import find_dotenv, load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Find the correct .env file based on the current environment
env = os.getenv("ENV", "development")
env_file = find_dotenv(f".env.{env}")

load_dotenv(env_file)


def get_email_config():
    return {
        "sender": os.getenv("EMAIL_SENDER_EMAIL"),
        "smtp_server": os.getenv("EMAIL_SMTP_SERVER"),
        "smtp_port": os.getenv("EMAIL_SMTP_PORT"),
        "username": os.getenv("EMAIL_USERNAME"),
        "password": os.getenv("EMAIL_PASSWORD"),
    }


def get_database_url():
    return os.getenv("DATABASE_URL", "sqlite:///sqlite.db")


def get_rate_limit_config():
    requests_per_minute = os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "6000")
    burst_limit = os.getenv("RATE_LIMIT_BURST", "10000")
    
    logger.info(f"DEBUG: RATE_LIMIT_REQUESTS_PER_MINUTE env var: {requests_per_minute}")
    logger.info(f"DEBUG: RATE_LIMIT_BURST env var: {burst_limit}")
    
    return {
        "requests_per_minute": int(requests_per_minute),
        "burst_limit": int(burst_limit),
    }


def get_cors_config():
    """Get CORS configuration from environment variables."""
    # Parse comma-separated allowed origins
    origins_str = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:8080,https://localhost:8080")
    allowed_origins = [origin.strip() for origin in origins_str.split(",") if origin.strip()]
    
    return {
        "allow_origins": allowed_origins,
        "allow_credentials": os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true",
        "allow_methods": os.getenv("CORS_ALLOW_METHODS", "GET,POST,PUT,PATCH,DELETE").split(","),
        "allow_headers": os.getenv("CORS_ALLOW_HEADERS", "Content-Type,Authorization").split(","),
    }
