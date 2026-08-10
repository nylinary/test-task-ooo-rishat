from pathlib import Path

from config.env import env, read_env_file

BASE_DIR = Path(__file__).resolve().parent.parent

read_env_file(BASE_DIR)

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

SECRET_KEY = env.str("DJANGO_SECRET_KEY", default="insecure-secret-key-for-local-development")

DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["*"])

CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# Railway (and most PaaS) terminate TLS in front of the app, so Django has to
# trust the forwarded protocol header to build correct absolute URLs - those
# end up in Stripe `success_url` / `cancel_url`.
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Railway exposes the public domain of the service as an env variable, which
# saves one manual configuration step after each deploy.
RAILWAY_PUBLIC_DOMAIN = env.str("RAILWAY_PUBLIC_DOMAIN", default="")

if RAILWAY_PUBLIC_DOMAIN:
    ALLOWED_HOSTS = [*ALLOWED_HOSTS, RAILWAY_PUBLIC_DOMAIN]
    CSRF_TRUSTED_ORIGINS = [*CSRF_TRUSTED_ORIGINS, f"https://{RAILWAY_PUBLIC_DOMAIN}"]

# HTTPS-only hardening. Off by default so that a plain-HTTP `docker compose up`
# keeps working; Railway serves over HTTPS, so it is enabled there automatically.
SECURE_HTTPS_ONLY = env.bool("DJANGO_SECURE_HTTPS_ONLY", default=bool(RAILWAY_PUBLIC_DOMAIN))

if SECURE_HTTPS_ONLY:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
]

LOCAL_APPS = [
    "shop.core",
    "shop.catalog",
    "shop.orders",
    "shop.payments",
    "shop.web",
]

INSTALLED_APPS = [*DJANGO_APPS, *THIRD_PARTY_APPS, *LOCAL_APPS]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES = {
    "default": env.db_url(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    ),
}

DATABASES["default"]["CONN_MAX_AGE"] = env.int("DATABASE_CONN_MAX_AGE", default=60)

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# I18N
# ---------------------------------------------------------------------------

LANGUAGE_CODE = "en-us"
TIME_ZONE = env.str("DJANGO_TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "shop.api.exception_handlers.application_exception_handler",
}

# ---------------------------------------------------------------------------
# Stripe
#
# One keypair per supported currency: the currency of an `Item` decides which
# Stripe account (and therefore which publishable key on the frontend) is used.
# Both currencies fall back to a single default keypair, so the project also
# runs with just `STRIPE_PUBLISHABLE_KEY` / `STRIPE_SECRET_KEY` set.
# ---------------------------------------------------------------------------

STRIPE_PUBLISHABLE_KEY = env.str("STRIPE_PUBLISHABLE_KEY", default="")
STRIPE_SECRET_KEY = env.str("STRIPE_SECRET_KEY", default="")

STRIPE_ACCOUNTS = {
    "usd": {
        "publishable_key": env.str("STRIPE_USD_PUBLISHABLE_KEY", default=STRIPE_PUBLISHABLE_KEY),
        "secret_key": env.str("STRIPE_USD_SECRET_KEY", default=STRIPE_SECRET_KEY),
    },
    "eur": {
        "publishable_key": env.str("STRIPE_EUR_PUBLISHABLE_KEY", default=STRIPE_PUBLISHABLE_KEY),
        "secret_key": env.str("STRIPE_EUR_SECRET_KEY", default=STRIPE_SECRET_KEY),
    },
}

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {"format": "{levelname} {asctime} {name} {message}", "style": "{"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple"},
    },
    "root": {"handlers": ["console"], "level": env.str("DJANGO_LOG_LEVEL", default="INFO")},
}
