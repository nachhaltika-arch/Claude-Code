"""
Configuration for KOMPAGNON backend.
Load from environment variables.
"""
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./kompagnon.db")

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
GOOGLE_PAGESPEED_API_KEY = os.getenv("GOOGLE_PAGESPEED_API_KEY")

# Email Configuration
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "info@kompagnon.de")
USE_MOCK_EMAIL = os.getenv("USE_MOCK_EMAIL", "false").lower() == "true"

# Application Settings
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Project Configuration
PROJECT_DEFAULTS = {
    "fixed_price": 2000.0,
    "hourly_rate": 45.0,
    "ai_tool_costs": 50.0,
    "target_hours": 8.5,
    "target_margin_percent": 78,
    "min_acceptable_margin_percent": 70,
}

# CORS
ALLOWED_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
]

# Scheduler
SCHEDULER_TIMEZONE = "Europe/Berlin"
SCHEDULER_JOB_STORE_URL = DATABASE_URL

# Validate critical configs
if not ANTHROPIC_API_KEY and ENVIRONMENT == "production":
    raise ValueError("ANTHROPIC_API_KEY not set in production")
