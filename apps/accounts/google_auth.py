"""
Connexion Google (OAuth2), implémentée directement plutôt qu'avec
django-allauth pour rester compatible avec le modèle `User` déjà en place
et le parcours d'inscription existant (vérification, complétion de
profil...).

Configuration requise (voir .env) :
    GOOGLE_CLIENT_ID=...
    GOOGLE_CLIENT_SECRET=...

Ces identifiants s'obtiennent depuis Google Cloud Console
(APIs & Services > Identifiants > Créer des identifiants > ID client OAuth,
type "Application Web"), avec comme URI de redirection autorisée :
    https://tondomaine/accounts/google/callback/
"""
import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse

from .models import User

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


def _redirect_uri(request):
    return request.build_absolute_uri(reverse("accounts:google_callback"))


def google_login_view(request):
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
    if not client_id:
        messages.error(request, "La connexion Google n'est pas configurée pour l'instant.")
        return redirect("accounts:login")

    state = secrets.token_urlsafe(24)
    request.session["google_oauth_state"] = state
    # On propage `next` à travers le flux OAuth pour rediriger correctement
    # ensuite (ex. quelqu'un qui clique "Continuer avec Google" depuis la
    # page d'une invitation).
    request.session["google_oauth_next"] = request.GET.get("next", "")

    params = {
        "client_id": client_id,
        "redirect_uri": _redirect_uri(request),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
    }
    return redirect(f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


def google_callback_view(request):
    client_id = getattr(settings, "GOOGLE_CLIENT_ID", "")
    client_secret = getattr(settings, "GOOGLE_CLIENT_SECRET", "")

    state = request.GET.get("state")
    expected_state = request.session.pop("google_oauth_state", None)
    next_url = request.session.pop("google_oauth_next", "") or "core:dashboard"

    if not state or state != expected_state:
        messages.error(request, "Session de connexion Google invalide, réessaie.")
        return redirect("accounts:login")

    code = request.GET.get("code")
    if not code:
        messages.error(request, "Connexion Google annulée ou refusée.")
        return redirect("accounts:login")

    try:
        token_res = requests.post(GOOGLE_TOKEN_URL, data={
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": _redirect_uri(request),
            "grant_type": "authorization_code",
        }, timeout=10)
        token_res.raise_for_status()
        access_token = token_res.json()["access_token"]

        userinfo_res = requests.get(
            GOOGLE_USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}, timeout=10,
        )
        userinfo_res.raise_for_status()
        profile = userinfo_res.json()
    except (requests.RequestException, KeyError, ValueError):
        messages.error(request, "Impossible de contacter Google pour le moment, réessaie plus tard.")
        return redirect("accounts:login")

    email = profile.get("email")
    if not email or not profile.get("email_verified"):
        messages.error(request, "Ton compte Google doit avoir une adresse e-mail vérifiée.")
        return redirect("accounts:login")

    user, created = User.objects.get_or_create(
        email__iexact=email,
        defaults={
            "username": email.split("@")[0] + "-" + secrets.token_hex(3),
            "email": email,
            "first_name": profile.get("given_name", "")[:150],
            "last_name": profile.get("family_name", "")[:150],
            # Google a déjà vérifié cette adresse e-mail : pas besoin de
            # repasser par le lien d'activation par e-mail.
            "is_verified": True,
        },
    )
    if created:
        user.set_unusable_password()
        user.save(update_fields=["password"])

    login(request, user)

    if not user.has_completed_profile:
        return redirect(f"{reverse('accounts:complete_profile')}?next={next_url}")
    return redirect(next_url)
