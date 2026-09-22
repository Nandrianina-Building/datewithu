from django.conf import settings


def analytics(request):
    """
    Expose la config Plausible aux templates (base.html). Le script n'est
    injecté que si PLAUSIBLE_DOMAIN est renseigné dans .env — désactivé
    par défaut, donc aucune requête externe tant que ce n'est pas configuré.
    """
    return {
        "plausible_domain": getattr(settings, "PLAUSIBLE_DOMAIN", ""),
        "plausible_script_url": getattr(settings, "PLAUSIBLE_SCRIPT_URL", ""),
    }
