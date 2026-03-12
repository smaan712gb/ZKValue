from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "zkvalue",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.verification_tasks",
        "app.workers.report_tasks",
        "app.workers.scheduling_tasks",
        "app.workers.blockchain_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 min hard limit
    task_soft_time_limit=540,  # 9 min soft limit
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Celery Beat — periodic task schedule
celery_app.conf.beat_schedule = {
    "process-due-schedules": {
        "task": "app.workers.scheduling_tasks.process_due_schedules",
        "schedule": crontab(minute="*/5"),  # Check every 5 minutes
    },
    "cleanup-old-verifications": {
        "task": "app.workers.report_tasks.cleanup_old_verifications",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM UTC
        "args": (90,),
    },
    "generate-monthly-usage-reports": {
        "task": "app.workers.scheduling_tasks.generate_all_usage_reports",
        "schedule": crontab(day_of_month=1, hour=6, minute=0),  # 1st of month at 6 AM
    },
    "daily-blockchain-anchor": {
        "task": "app.workers.blockchain_tasks.daily_blockchain_anchor",
        "schedule": crontab(hour=23, minute=55),  # Daily at 11:55 PM UTC
    },
}
