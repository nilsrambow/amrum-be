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
    raw = os.getenv("CORS_ALLOWED_ORIGINS")
    allowed_origins = [o.strip() for o in raw.split(",")] if raw else []
    allowed_origins = [o for o in allowed_origins if o]
    if not allowed_origins:
        print("No CORS_ALLOWED_ORIGINS found in environment variables")
    return {
        "allow_origins": allowed_origins,
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


def get_kurkarten_config():
    return {
        "kennung": os.getenv("KURKARTEN_KENNUNG"),
        "passwort": os.getenv("KURKARTEN_PASSWORT"),
        "ort": os.getenv("KURKARTEN_ORT"),
        "hotel": os.getenv("KURKARTEN_HOTEL"),
    }
