"""
Configuration Django — Date With U 🇲🇬❤️
Phase 1 : Fondation (auth, models de base, dashboard admin)
"""
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

# --- Sécurité -----------------------------------------------------------
SECRET_KEY = env("SECRET_KEY", default="change-me-in-.env")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

# URL de l'admin Django déplacée hors de /admin/ par défaut (évite le
# bruteforce/scan automatisé sur le chemin le plus connu de tous). À définir
# dans .env en production, ex: ADMIN_URL_PATH=gestion-x9f2/
ADMIN_URL_PATH = env("ADMIN_URL_PATH", default="admin/")

# Cookies de session / CSRF : jamais accessibles en JS, jamais envoyés en
# clair dès que le site tourne en HTTPS (post-déploiement, DEBUG=False).
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14  # 14 jours
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG

# En-têtes de sécurité navigateur.
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"

# HTTPS forcé + HSTS uniquement hors DEBUG (le serveur de dev local n'a pas
# de certificat TLS ; forcer la redirection casserait le développement).
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not DEBUG)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https") if not DEBUG else None
SECURE_HSTS_SECONDS = 0 if DEBUG else 60 * 60 * 24 * 365
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# Limites d'upload (empêche les gros fichiers de saturer le serveur — les
# images de profil/lieux sont en plus validées par Pillow + nos validators).
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024        # 5 Mo
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024
FILE_UPLOAD_PERMISSIONS = 0o644

# --- Applications ---------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Tiers
    "rest_framework",
    # Apps locales
    "apps.accounts",
    "apps.core",
    # Phase 2 — Contenu administrable
    "apps.locations",
    "apps.catalog",
    "apps.activities",
    "apps.moods",
    "apps.budgets",
    "apps.occasions",
    "apps.api",
    # Phase 3 — Date Builder
    "apps.planner",
    # Phase 4 — Invitations
    "apps.invitations",
    # Phase 5 — Dashboard utilisateur
    "apps.favorites",
    "apps.notifications",
    # Phase 7 — Communication
    "apps.chat",
    # Phase 8 — Fonctionnalités avancées
    "apps.packages",
    "apps.reviews",
    # Fonctionnalités "professionnelles" ajoutées après-coup : sécurité
    # (blocage/signalement), attendue sur toute plateforme mettant en
    # relation des inconnus.
    "apps.safety",
    # Fonctionnalités "pro" : monétisation, partenaires, contenu éditorial,
    # sécurité avancée.
    "apps.premium",
    "apps.partners",
    "apps.promos",
    "apps.safeshare",
    "apps.blog",
    "apps.feed",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.security.SecurityHeadersMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.analytics",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# --- Base de données ------------------------------------------------------
# Phase 1 : PostgreSQL via DATABASE_URL dans .env
# Exemple : postgres://user:password@localhost:5432/datewithu
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default="sqlite:///" + str(BASE_DIR / "db.sqlite3"),
    )
}

# --- Authentification -------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "core:dashboard"
LOGOUT_REDIRECT_URL = "core:home"

# --- Internationalisation ------------------------------------------------
LANGUAGE_CODE = "fr"
TIME_ZONE = "Indian/Antananarivo"
USE_I18N = True
USE_TZ = True

# --- Fichiers statiques et médias -----------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework (prêt pour les phases suivantes / AJAX) --------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "invitation-respond": "20/hour",
        "invitation-public": "60/hour",
        "auth-sensitive": "10/hour",
        "report-user": "10/hour",
    },
    # Pagination des ViewSets en lecture (villes, lieux, activités...) pour
    # permettre une recherche + un "Voir plus" en AJAX plutôt que de tout
    # renvoyer d'un bloc. Le frontend gère déjà les deux formats de réponse
    # (`data.results || data`), donc l'activer ici est rétro-compatible.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 12,
}

# --- E-mail (vérification de compte, notifications) -----------------------
# Par défaut : backend "console" (les mails s'affichent dans les logs du
# serveur de dev). En prod, configurer un vrai SMTP via les variables .env.
EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend" if DEBUG
    else "django.core.mail.backends.smtp.EmailBackend",
)
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Date With U <no-reply@datewithu.mg>")

# --- Analytics (Plausible, sans cookie) ------------------------------------
# Plausible ne dépose aucun cookie et n'identifie pas les visiteurs
# individuellement : aucune bannière de consentement n'est nécessaire pour
# l'utiliser (contrairement à Google Analytics). Laisser vide désactive
# proprement le script (aucune requête externe ajoutée tant que ce n'est
# pas configuré). Pour l'activer : définir PLAUSIBLE_DOMAIN=datewithu.mg
# dans .env (et éventuellement PLAUSIBLE_SCRIPT_URL si auto-hébergé).
PLAUSIBLE_DOMAIN = env("PLAUSIBLE_DOMAIN", default="")
PLAUSIBLE_SCRIPT_URL = env(
    "PLAUSIBLE_SCRIPT_URL", default="https://plausible.io/js/script.js"
)

# --- Connexion Google (OAuth2) ---------------------------------------------
# Laisser vide désactive proprement le bouton "Continuer avec Google"
# (voir apps/accounts/google_auth.py pour la marche à suivre).
GOOGLE_CLIENT_ID = env("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = env("GOOGLE_CLIENT_SECRET", default="")

# Durée de validité du lien de vérification d'e-mail (secondes).
EMAIL_VERIFICATION_TIMEOUT = env.int("EMAIL_VERIFICATION_TIMEOUT", default=60 * 60 * 24)  # 24h

# --- Cache (sert de backend au rate-limiting maison, apps/core/security.py) --
CACHES = {
    "default": env.cache("CACHE_URL", default="locmemcache://"),
}
