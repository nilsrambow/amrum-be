import os

from dotenv import find_dotenv, load_dotenv

# Find the correct .env file based on the current environment
env = os.getenv("ENV", "development")
env_file = find_dotenv(f".env.{env}")
print(env_file)

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
    return os.getenv("DATABASE_URL")
