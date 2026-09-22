"""
Tokens de vérification d'e-mail.

On utilise `django.core.signing` (HMAC signé avec SECRET_KEY) plutôt qu'une
table dédiée : le token encode l'id utilisateur + une empreinte dérivée de
son état courant (e-mail, mot de passe, statut vérifié). Dès que l'un de
ces éléments change — l'utilisateur vérifie son compte, change d'e-mail ou
de mot de passe — l'ancien lien devient automatiquement invalide, sans job
de nettoyage à prévoir. La signature elle-même empêche toute falsification
côté client (elle dépend de SECRET_KEY, jamais exposé).
"""
import hashlib

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import signing

SALT = "accounts.email-verification"


def _fingerprint(user):
    raw = f"{user.pk}:{user.email}:{user.password}:{user.is_verified}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def make_token(user):
    return signing.dumps({"uid": user.pk, "fp": _fingerprint(user)}, salt=SALT)


def user_from_token(token):
    """
    Vérifie la signature + l'expiration + que rien n'a changé depuis
    l'émission du token, puis renvoie l'utilisateur correspondant (ou None).
    """
    max_age = getattr(settings, "EMAIL_VERIFICATION_TIMEOUT", 60 * 60 * 24)
    try:
        data = signing.loads(token, salt=SALT, max_age=max_age)
    except signing.BadSignature:
        return None

    User = get_user_model()
    user = User.objects.filter(pk=data.get("uid")).first()
    if user is None or _fingerprint(user) != data.get("fp"):
        return None
    return user
