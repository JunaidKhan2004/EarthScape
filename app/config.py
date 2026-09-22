import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/earthscape")

    HDFS_ROOT = os.path.join(BASE_DIR, "app", "hdfs_sim")
    HDFS_RAW = os.path.join(HDFS_ROOT, "raw")
    HDFS_PROCESSED = os.path.join(HDFS_ROOT, "processed")

    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.environ.get("GMAIL_USER")
    MAIL_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")
    MAIL_DEFAULT_SENDER = (
        "EarthScape Climate Agency",
        os.environ.get("GMAIL_USER", "no-reply@earthscape.local"),
    )

    RESET_TOKEN_MAX_AGE_SECONDS = 3600  # 1 hour

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload size
