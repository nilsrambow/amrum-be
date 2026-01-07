import os

from dotenv import find_dotenv, load_dotenv

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
    
    return {
        "requests_per_minute": int(requests_per_minute),
        "burst_limit": int(burst_limit),
    }


def get_cors_config():
    """Get CORS configuration - hardcoded values."""
    return {
        "allow_origins": [
            "http://192.168.178.42:6333",
            "http://homeserver.lan:7000",
            "https://homeserver.lan:7000",
            "http://192.168.178.42:7000",
            "https://192.168.178.42:7000",
            "https://rambow09.dedyn.io",
            "http://rambow09.dedyn.io",
        ],
        "allow_credentials": False,
        "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Content-Type",
            "Authorization",
            "Accept",
            "Accept-Language",
            "Content-Language",
            "X-Requested-With",
        ],
    }
