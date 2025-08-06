# app/config.py
import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379")

# Initialize Celery with proper configuration
celery_app = Celery(
    "gemini_tasks", 
    broker=os.getenv("REDIS_URL"),
    backend=os.getenv("REDIS_URL")  # Add result backend
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(['app.tasks'])

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PRICE_ID = os.getenv("STRIPE_PRICE_ID")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"

OTP_EXPIRY_SECONDS = 300