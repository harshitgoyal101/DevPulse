"""Shared Django settings."""

from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

import os

BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Repo root is one level above backend/
_REPO_ROOT = BASE_DIR.parent
load_dotenv(_REPO_ROOT / ".env")


def _parse_allowed_hosts(raw: str) -> list[str]:
    return [h.strip() for h in raw.split(",") if h.strip()]


def _database_from_url(url: str) -> dict:
    parsed = urlparse(url)
    if parsed.scheme not in ("postgres", "postgresql"):
        raise ImproperlyConfigured(
            f"DATABASE_URL must use postgres:// scheme, got: {parsed.scheme}",
        )
    path = parsed.path or ""
    name = path[1:] if path.startswith("/") else path
    if not name:
        raise ImproperlyConfigured("DATABASE_URL must include database name.")
    port = parsed.port or 5432
    return {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": name,
        "USER": parsed.username or "",
        "PASSWORD": parsed.password or "",
        "HOST": parsed.hostname or "",
        "PORT": str(port),
    }


_settings_module = os.environ.get("DJANGO_SETTINGS_MODULE", "")
_test_settings = _settings_module.endswith(".test")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if _test_settings:
        SECRET_KEY = "django-insecure-test-only"
    else:
        raise ImproperlyConfigured("Set DJANGO_SECRET_KEY environment variable.")

DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in ("1", "true", "yes")

ALLOWED_HOSTS = _parse_allowed_hosts(os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1"))

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "apps.accounts",
    "apps.organizations",
    "apps.ingestion",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

_database_url = os.environ.get("DATABASE_URL")
if not _database_url and not _test_settings:
    raise ImproperlyConfigured("Set DATABASE_URL environment variable.")
if _database_url:
    DATABASES = {"default": _database_from_url(_database_url)}
else:
    DATABASES = {}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
}
