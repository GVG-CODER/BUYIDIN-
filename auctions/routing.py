from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/your_websocket_path/$', consumers.YourConsumer.as_asgi()),
]