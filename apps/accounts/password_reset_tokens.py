"""
Tokens de réinitialisation de mot de passe — même approche que
`tokens.py` (signature HMAC via `django.core.signing`, sans table dédiée).

L'empreinte est dérivée du hash du mot de passe courant : dès que le mot
de passe change (via ce lien ou par un autre moyen), l'ancien lien devient
automatiquement invalide, ce qui empêche de le réutiliser deux fois ou
après un changement de mot de passe entre-temps.
"""
import hashlib

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing

SALT = "accounts.password-reset"


def _fingerprint(user):
    raw = f"{user.pk}:{user.password}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def make_token(user):
    return signing.dumps({"uid": user.pk, "fp": _fingerprint(user)}, salt=SALT)


def user_from_token(token):
    """
    Vérifie la signature + l'expiration + que le mot de passe n'a pas
    changé depuis l'émission du lien, puis renvoie l'utilisateur (ou None).
    """
    max_age = getattr(settings, "PASSWORD_RESET_TIMEOUT_CUSTOM", 60 * 60)  # 1h
    try:
        data = signing.loads(token, salt=SALT, max_age=max_age)
    except signing.BadSignature:
        return None

    User = get_user_model()
    user = User.objects.filter(pk=data.get("uid")).first()
    if user is None or _fingerprint(user) != data.get("fp"):
        return None
    return user
