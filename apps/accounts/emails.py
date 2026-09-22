from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from .tokens import make_token


def send_verification_email(request, user):
    token = make_token(user)
    path = reverse("accounts:verify_email", kwargs={"token": token})
    verify_url = request.build_absolute_uri(path)

    context = {"user": user, "verify_url": verify_url}
    subject = "Confirme ton adresse e-mail — Date With U"
    text_body = render_to_string("accounts/emails/verify_email.txt", context)

    send_mail(
        subject,
        text_body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )


def send_password_reset_email(request, user):
    from .password_reset_tokens import make_token as make_reset_token

    token = make_reset_token(user)
    path = reverse("accounts:password_reset_confirm", kwargs={"token": token})
    reset_url = request.build_absolute_uri(path)

    context = {"user": user, "reset_url": reset_url}
    subject = "Réinitialise ton mot de passe — Date With U"
    text_body = render_to_string("accounts/emails/password_reset.txt", context)

    send_mail(
        subject,
        text_body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
