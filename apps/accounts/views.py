from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeDoneView, PasswordChangeView,
)
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.http import url_has_allowed_host_and_scheme

from apps.core.security import rate_limit

from .emails import send_password_reset_email, send_verification_email
from .forms import (
    CompleteProfileForm, PasswordResetRequestForm, ProfileForm, RegisterForm,
    SetNewPasswordForm,
)
from .password_reset_tokens import user_from_token as password_reset_user_from_token
from .tokens import user_from_token


def _safe_next(request):
    """
    Renvoie la valeur de `next` (GET ou POST) si — et seulement si — elle
    pointe vers notre propre site. Empêche les redirections ouvertes
    (open redirect) qui pourraient servir à des liens de phishing du type
    /accounts/login/?next=https://site-pirate.example.
    """
    candidate = request.POST.get("next") or request.GET.get("next")
    if candidate and url_has_allowed_host_and_scheme(
        candidate, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return candidate
    return None


def _with_next(view_name, next_url):
    """Construit l'URL de `view_name`, avec `?next=...` si on en a un à propager."""
    url = reverse(view_name)
    return f"{url}?next={next_url}" if next_url else url


def _post_verification_redirect(user, next_url):
    """
    Où envoyer un utilisateur déjà vérifié : direction le dashboard (ou la
    page `next` demandée), sauf s'il lui manque encore les infos
    obligatoires du profil — auquel cas on l'arrête d'abord là.
    """
    if not user.has_completed_profile:
        return _with_next("accounts:complete_profile", next_url)
    return next_url or reverse("core:dashboard")


class DateWithULoginView(LoginView):
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    @method_decorator(rate_limit("login", limit=10, window_seconds=300))
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["google_login_enabled"] = bool(settings.GOOGLE_CLIENT_ID)
        return context


class DateWithULogoutView(LogoutView):
    next_page = "core:home"


@rate_limit("register", limit=8, window_seconds=600)
def register_view(request):
    if request.user.is_authenticated:
        return redirect("core:dashboard")

    from apps.core.models import SiteConfiguration
    if not SiteConfiguration.load().registration_enabled:
        messages.error(request, "Les inscriptions sont temporairement fermées.")
        return redirect("core:home")

    next_url = _safe_next(request)

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            try:
                send_verification_email(request, user)
                messages.success(
                    request,
                    "Bienvenue sur Date With U ! Un e-mail de confirmation vient de "
                    "t'être envoyé — clique sur le lien qu'il contient pour activer "
                    "ton compte et accéder à ton espace.",
                )
            except Exception:
                messages.warning(
                    request,
                    "Ton compte est créé, mais l'e-mail de confirmation n'a pas pu "
                    "être envoyé pour le moment. Tu pourras le redemander depuis cette page.",
                )
            # On ne dirige plus jamais directement vers le dashboard : il faut
            # d'abord cliquer le lien d'activation reçu par e-mail (et ensuite
            # compléter les infos obligatoires du profil, voir
            # `complete_profile_view`).
            return redirect(_with_next("accounts:verify_pending", next_url))
    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {
        "form": form, "next": next_url or "",
        "google_login_enabled": bool(settings.GOOGLE_CLIENT_ID),
    })


@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            email_changed = form.cleaned_data["email"] != request.user.email
            user = form.save(commit=False)
            if email_changed:
                # Changer d'adresse invalide la vérification précédente :
                # on ne veut jamais qu'un compte reste "vérifié" pour une
                # adresse que son titulaire ne contrôle plus.
                user.is_verified = False
            user.save()
            form.save_m2m()
            messages.success(request, "Profil mis à jour.")
            if email_changed:
                try:
                    send_verification_email(request, user)
                    messages.info(request, "Nouvelle adresse e-mail : merci de la reconfirmer.")
                except Exception:
                    pass
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile.html", {"form": form})


@login_required
def profile_edit_view(request):
    """
    Formulaire de modification du profil — volontairement séparé de la
    page d'affichage (accounts:profile), qui doit rester une vue "propre"
    façon Instagram sans champs de saisie mélangés au contenu.
    """
    if request.method == "POST":
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            email_changed = form.cleaned_data["email"] != request.user.email
            user = form.save(commit=False)
            if email_changed:
                user.is_verified = False
            user.save()
            form.save_m2m()
            messages.success(request, "Profil mis à jour.")
            if email_changed:
                try:
                    send_verification_email(request, user)
                    messages.info(request, "Nouvelle adresse e-mail : merci de la reconfirmer.")
                except Exception:
                    pass
            return redirect("accounts:profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(request, "accounts/profile_edit.html", {"form": form})


@login_required
def public_profile_view(request, user_id):
    """
    Profil public minimal d'un·e autre utilisateur·rice — accessible
    depuis le chat (« voir son profil ») pour savoir à qui l'on parle.
    On n'expose volontairement que le nom, l'avatar et la bio : jamais
    l'e-mail, le téléphone ou la date de naissance, qui restent privés.
    """
    from django.db.models import Avg
    from django.shortcuts import get_object_or_404

    from apps.reviews.models import DateRating
    from apps.safety.models import Block

    User = get_user_model()
    profile_user = get_object_or_404(User, pk=user_id)
    is_blocked = (
        request.user.is_authenticated
        and Block.objects.filter(user=request.user, blocked_user=profile_user).exists()
    )
    reliability = DateRating.objects.filter(rated_user=profile_user).aggregate(avg=Avg("stars"))
    reliability_avg = round(reliability["avg"], 1) if reliability["avg"] else None
    reliability_count = DateRating.objects.filter(rated_user=profile_user).count()
    return render(request, "accounts/public_profile.html", {
        "profile_user": profile_user,
        "is_blocked": is_blocked,
        "reliability_avg": reliability_avg,
        "reliability_count": reliability_count,
    })


@rate_limit("verify-email", limit=20, window_seconds=600)
def verify_email_view(request, token):
    user = user_from_token(token)
    if user is None:
        return render(request, "accounts/verify_invalid.html", status=400)

    user.is_verified = True
    user.save(update_fields=["is_verified"])
    messages.success(request, "Adresse e-mail confirmée. Merci !")

    if request.user.is_authenticated and request.user.pk == user.pk:
        next_url = _safe_next(request)
        return redirect(_post_verification_redirect(user, next_url))

    return render(request, "accounts/verify_success.html")


@login_required
def verify_pending_view(request):
    """
    Écran affiché juste après l'inscription (et tant que le compte n'est
    pas vérifié) : on explique qu'il faut cliquer le lien reçu par e-mail
    avant de pouvoir accéder au dashboard.
    """
    next_url = _safe_next(request)
    if request.user.is_verified:
        return redirect(_post_verification_redirect(request.user, next_url))
    return render(request, "accounts/verify_pending.html", {"next": next_url or ""})


@login_required
def complete_profile_view(request):
    """
    Dernière étape obligatoire avant le dashboard : renseigner prénom,
    nom, téléphone et date de naissance (voir `User.REQUIRED_PROFILE_FIELDS`).
    """
    next_url = _safe_next(request)

    if not request.user.is_verified:
        return redirect(_with_next("accounts:verify_pending", next_url))

    if request.user.has_completed_profile:
        return redirect(next_url or "core:dashboard")

    if request.method == "POST":
        form = CompleteProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profil complété — bienvenue dans ton espace !")
            return redirect(next_url or "core:dashboard")
    else:
        form = CompleteProfileForm(instance=request.user)

    return render(request, "accounts/complete_profile.html", {"form": form, "next": next_url or ""})


@login_required
@rate_limit("resend-verification", limit=5, window_seconds=600)
def resend_verification_view(request):
    if request.user.is_verified:
        messages.info(request, "Ton compte est déjà vérifié.")
        return redirect("accounts:profile")

    try:
        send_verification_email(request, request.user)
        messages.success(request, "E-mail de confirmation renvoyé — pense à vérifier tes spams.")
    except Exception:
        messages.error(request, "Impossible d'envoyer l'e-mail pour le moment, réessaie plus tard.")

    referer = request.META.get("HTTP_REFERER") or ""
    if referer and url_has_allowed_host_and_scheme(
        referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        return redirect(referer)
    return redirect("accounts:profile")


@rate_limit("password-reset-request", limit=6, window_seconds=600)
def password_reset_request_view(request):
    """
    Étape 1 du mot de passe oublié : on demande l'e-mail et on envoie un
    lien si un compte correspond — sans jamais révéler si l'adresse existe
    ou non (le message affiché est volontairement identique dans les deux
    cas, pour ne pas servir à énumérer les comptes existants).
    """
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            User = get_user_model()
            user = User.objects.filter(email__iexact=form.cleaned_data["email"]).first()
            if user is not None:
                try:
                    send_password_reset_email(request, user)
                except Exception:
                    pass  # on ne révèle jamais un échec d'envoi côté public
            return redirect("accounts:password_reset_sent")
    else:
        form = PasswordResetRequestForm()
    return render(request, "accounts/password_reset_request.html", {"form": form})


def password_reset_sent_view(request):
    return render(request, "accounts/password_reset_sent.html")


@rate_limit("password-reset-confirm", limit=20, window_seconds=600)
def password_reset_confirm_view(request, token):
    """Étape 2 : vérifie le lien reçu par e-mail et permet de choisir un nouveau mot de passe."""
    user = password_reset_user_from_token(token)
    if user is None:
        return render(request, "accounts/password_reset_invalid.html", status=400)

    if request.method == "POST":
        form = SetNewPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Mot de passe mis à jour — tu peux maintenant te connecter.")
            return redirect("accounts:login")
    else:
        form = SetNewPasswordForm(user)
    return render(request, "accounts/password_reset_confirm.html", {"form": form})


class DateWithUPasswordChangeView(PasswordChangeView):
    """Changer son mot de passe en étant déjà connecté (jusqu'ici, seule la
    réinitialisation par e-mail existait — un oubli assez classique)."""

    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:password_change_done")


class DateWithUPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = "accounts/password_change_done.html"


@login_required
def delete_account_view(request):
    """
    Suppression définitive du compte, avec confirmation explicite du mot de
    passe (on n'agit pas sur une simple case à cocher pour une action aussi
    irréversible). Les rendez-vous déjà partagés restent visibles pour
    l'autre partie (creator/partner_user passe à NULL via on_delete côté
    modèles), mais toutes les informations personnelles disparaissent.
    """
    if request.method == "POST":
        password = request.POST.get("password", "")
        if not request.user.check_password(password):
            messages.error(request, "Mot de passe incorrect — ton compte n'a pas été supprimé.")
            return redirect("accounts:delete_account")
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "Ton compte a été supprimé définitivement. À bientôt peut-être !")
        return redirect("core:home")
    return render(request, "accounts/delete_account.html")
