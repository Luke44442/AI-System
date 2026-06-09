from __future__ import annotations
from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "scentara",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,
    beat_schedule={
        "sync-marketplace-listings": {
            "task": "app.workers.tasks.sync_all_marketplace_listings",
            "schedule": crontab(minute=0, hour="*/6"),
        },
        "refresh-analytics-views": {
            "task": "app.workers.tasks.refresh_analytics_views",
            "schedule": crontab(minute=0, hour=1),
        },
        "update-inventory-status": {
            "task": "app.workers.tasks.update_inventory_status",
            "schedule": crontab(minute=30, hour="*/4"),
        },
        "generate-sitemap": {
            "task": "app.workers.tasks.generate_sitemap",
            "schedule": crontab(minute=0, hour=2),
        },
    },
)
