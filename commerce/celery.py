import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'commerce.settings')

app = Celery('BUYIDIN')
app.autodiscover_tasks()

# Broker and result backend configuration
app.conf.broker_url = 'redis://localhost:6379/0'  #using Redis as the broker
app.conf.result_backend = 'redis://localhost:6379/0'

app.conf.task_routes = {
    'myapp.tasks.start_auction_session': {'queue': 'auctions'},
    'myapp.tasks.end_auction_session': {'queue': 'auctions'},
}

#set Time zone
app.conf.timezone = 'UTC'

#Configure periodic tasks
app.conf.beat_schedule = {
    'start_auction': {
        'task': 'myapp.tasks.start_auction_session',
        'schedule': crontab(hour=0, minute=0, day_of_week=1),  # Every Monday at midnight
    },
    'end_auction': {
        'task': 'myapp.tasks.end_auction_session',
        'schedule': crontab(hour=12, minute=0, day_of_week=1),  # Every Monday at noon
    },
}