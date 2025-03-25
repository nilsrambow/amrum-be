import os

from dotenv import load_dotenv

load_dotenv()


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
