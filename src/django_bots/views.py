"""A robots.txt view with rules for AI bots."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_safe

__all__ = ["robots_txt"]


@require_safe
@cache_control(max_age=86400)
def robots_txt(request: HttpRequest) -> HttpResponse:
    """Render the ``django_bots/robots.txt`` template as plain text."""
    return render(
        request, "django_bots/robots.txt", content_type="text/plain; charset=utf-8"
    )
