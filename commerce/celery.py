import os
from celery import Celery
from celery.schedules import crontab  # Import crontab here

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'commerce.settings')

app = Celery('BUYIDIN')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Broker and result backend configuration
app.conf.broker_url = 'redis://localhost:6379/0'  # Example using Redis as the broker
app.conf.result_backend = 'redis://localhost:6379/0'  # Optional: Where to store the results

# Example of custom task settings
app.conf.task_routes = {
    'myapp.tasks.start_auction_session': {'queue': 'auctions'},
}

# Optional: Time zone
app.conf.timezone = 'UTC'

# Optional: Configure periodic tasks
app.conf.beat_schedule = {
    'start_auction': {
        'task': 'myapp.tasks.start_auction_session',
        'schedule': crontab(hour=0, minute=0, day_of_week=1),  # Run every Monday at midnight
    },
    'end_auction': {
        'task': 'myapp.tasks.end_auction_session',
        'schedule': crontab(hour=23, minute=59, day_of_week=2),  # Run every Tuesday at 11:59 PM
    },
}