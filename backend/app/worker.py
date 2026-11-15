import os

from celery import Celery

celery_app = Celery(
    "indrastra_harvester",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/1"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/2"),
    include=[
        "backend.app.harvest.tasks",
        "backend.app.harvest.schedules",
        "backend.app.search.tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,
    broker_transport_options={"visibility_timeout": 3900},
    beat_schedule={
        "dispatch-due-harvest-schedules": {
            "task": "harvest.dispatch_due_schedules",
            "schedule": 60.0,
        }
    },
)
