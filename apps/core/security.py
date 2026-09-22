"""
Utilitaires de sécurité transverses.

On évite volontairement une dépendance externe (django-axes, django-ratelimit...)
pour ce projet : le cache Django (backend mémoire par défaut, Redis/memcached
en prod via CACHE_URL) suffit à limiter les abus sur les endpoints sensibles
(connexion, inscription, réponse à une invitation, renvoi d'e-mail...).
"""
import functools
import time

from django.core.cache import cache
from django.http import HttpResponseForbidden


def _client_ip(request):
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def rate_limit(key_prefix, limit=5, window_seconds=300):
    """
    Décorateur pour vues Django "classiques" (pas DRF) : limite `limit`
    requêtes par `window_seconds` secondes, par IP. Utilisé sur les vues
    d'authentification pour ralentir le bruteforce / le spam d'inscriptions.
    """
    def decorator(view_func):
        @functools.wraps(view_func)
        def wrapped(request, *args, **kwargs):
            ip = _client_ip(request)
            cache_key = f"ratelimit:{key_prefix}:{ip}"
            history = cache.get(cache_key, [])
            now = time.time()
            history = [t for t in history if now - t < window_seconds]
            if len(history) >= limit:
                return HttpResponseForbidden(
                    "Trop de tentatives. Merci de réessayer dans quelques minutes."
                )
            history.append(now)
            cache.set(cache_key, history, timeout=window_seconds)
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


class SecurityHeadersMiddleware:
    """
    Ajoute quelques en-têtes que `SecurityMiddleware` ne couvre pas nativement :
    - Permissions-Policy : désactive les API navigateur sensibles non utilisées.
    - X-Permitted-Cross-Domain-Policies : bloque les anciens plugins Flash/PDF.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response.setdefault(
            "Permissions-Policy",
            "geolocation=(self), camera=(), microphone=(), payment=(), usb=()",
        )
        response.setdefault("X-Permitted-Cross-Domain-Policies", "none")
        return response
