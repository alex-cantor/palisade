"""
ASGI config for core project.

WebSocket connections to /ws/console/ are handled by our PVE proxy.
All other traffic is handled by Django's standard ASGI application.
"""
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

from django.core.asgi import get_asgi_application  # noqa: E402 (must be after setdefault)
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler

_django_app = ASGIStaticFilesHandler(get_asgi_application())


async def application(scope, receive, send):
    if scope["type"] == "websocket" and scope.get("path", "").startswith("/ws/console/"):
        from core.ws_proxy import console_ws_handler
        await console_ws_handler(scope, receive, send)
    else:
        await _django_app(scope, receive, send)
