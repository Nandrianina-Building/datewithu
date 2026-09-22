import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()

# Phase 7 (Communication) : on remplacera cette application par un
# ProtocolTypeRouter Django Channels pour gérer le chat et les
# notifications temps réel en WebSocket.
