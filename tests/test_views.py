from __future__ import annotations

import pytest
from django.test import override_settings

from django_bots.ai import robots_rules
from django_bots.views import robots_txt

EXTENDED = """{% extends "django_bots/robots.txt" %}{% block rules %}
User-agent: *
Disallow: /admin/

Sitemap: https://example.com/sitemap.xml
{% endblock %}"""


@pytest.mark.parametrize("method", ["get", "head"])
def test_robots_txt(rf, method):
    request = getattr(rf, method)("/robots.txt")

    response = robots_txt(request)

    assert response.status_code == 200
    assert response["Content-Type"] == "text/plain; charset=utf-8"
    assert response["Cache-Control"] == "max-age=86400"


def test_robots_txt_content(rf):
    response = robots_txt(rf.get("/robots.txt"))

    assert response.content.decode() == robots_rules() + "\n"


@pytest.mark.parametrize("method", ["post", "put", "delete"])
def test_robots_txt_rejects_unsafe_methods(rf, method):
    request = getattr(rf, method)("/robots.txt")

    response = robots_txt(request)

    assert response.status_code == 405
    assert response["Allow"] == "GET, HEAD"


def test_robots_txt_allow_setting(rf):
    with override_settings(BOTS_AI_ALLOW=["GPTBot"]):
        response = robots_txt(rf.get("/robots.txt"))

    assert b"GPTBot" not in response.content
    assert b"User-agent: ClaudeBot\n" in response.content


def test_robots_txt_extended_template(rf, settings):
    settings.TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "OPTIONS": {
                "loaders": [
                    (
                        "django.template.loaders.locmem.Loader",
                        {"django_bots/robots.txt": EXTENDED},
                    ),
                    "django.template.loaders.app_directories.Loader",
                ],
            },
        }
    ]

    response = robots_txt(rf.get("/robots.txt"))

    assert response.content.decode() == (
        robots_rules()
        + "\n\nUser-agent: *\nDisallow: /admin/\n\nSitemap: https://example.com/sitemap.xml\n"
    )
