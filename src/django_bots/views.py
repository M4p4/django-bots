"""A robots.txt view with rules for AI bots."""

from __future__ import annotations

from django.http import HttpRequest, HttpResponse
from django.template import TemplateDoesNotExist, loader
from django.views.decorators.cache import cache_control
from django.views.decorators.http import require_safe

from django_bots.ai import robots_rules

__all__ = ["robots_txt"]


@require_safe
@cache_control(max_age=86400)
def robots_txt(request: HttpRequest) -> HttpResponse:
    """Render the ``django_bots/robots.txt`` template as plain text.

    Without a template engine that finds it, for example in an API-only project, the
    rules are served as they are.
    """
    try:
        template = loader.get_template("django_bots/robots.txt")
    except TemplateDoesNotExist:
        content = robots_rules() + "\n"
    else:
        content = template.render(request=request)
    return HttpResponse(content, content_type="text/plain; charset=utf-8")
