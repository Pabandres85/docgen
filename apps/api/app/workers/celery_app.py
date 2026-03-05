from celery import Celery
from app.core.settings import settings

celery_app = Celery(
    "docgen",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.task_track_started = True
celery_app.conf.result_expires = 3600
