import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Structural App Configurations
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-key')

# Core Relational Database Matrices
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE")

# Google Sign-In Third-Party Auth Integrations
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")

# SMTP Email Configuration (For sending OTP registration verification codes via Gmail)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")