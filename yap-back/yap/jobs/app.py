import os
from celery import Celery


celery_app = Celery(
    'yap_tasks',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379'),
)
