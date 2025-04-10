from celery import Celery

from app.core.config import settings

app = Celery(
    "style",
    broker=settings.CELERY_BROKER_URI,
    backend=settings.CELERY_BACKEND_URI,
    result_expires=settings.CELERY_RESULT_EXPIRES,
    broker_transport_options={
        "visibility_timeout": 3600 * 100  # 100 hours in seconds
    },
    # worker_max_tasks_per_child=2,
    # task_acks_late=True, # Enable if you want to dequeue the task after the task has been executed. Be careful
    # broker_connection_retry_on_startup=False,
)
