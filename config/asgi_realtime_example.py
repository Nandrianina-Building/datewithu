"""
Exemple de config/asgi.py une fois `channels` + `channels-redis` installés
et Redis disponible. Pour activer :

    pip install channels channels-redis daphne
    # renseigne REDIS_URL dans .env
    cp config/asgi_realtime_example.py config/asgi.py
    # ajoute "channels" et "daphne" à INSTALLED_APPS (settings.py),
    # et CHANNEL_LAYERS (voir README, section "Chat temps réel")

Puis lance avec Daphne au lieu de `runserver` :
    daphne -b 0.0.0.0 -p 8000 config.asgi:application
"""
import os

import django
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.chat.routing import websocket_urlpatterns  # noqa: E402

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})
