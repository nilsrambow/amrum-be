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
    return {
        "requests_per_minute": int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60")),
        "burst_limit": int(os.getenv("RATE_LIMIT_BURST", "100")),
    }
