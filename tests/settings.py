from __future__ import annotations

SECRET_KEY = "django-bots-tests"

INSTALLED_APPS = ["django_bots"]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
    }
]
