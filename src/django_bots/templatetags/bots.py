"""Crawler and AI bot filters, the ``ai_robots_rules`` tag, and every ``user_agents`` filter."""

from __future__ import annotations

from django import template
from django.http import HttpRequest
from django.utils.safestring import SafeString, mark_safe

from django_bots.ai import robots_rules
from django_bots.templatetags import user_agents
from django_bots.utils import get_and_set_user_agent

register = template.Library()
register.filters.update(user_agents.register.filters)


@register.filter
def is_crawler(request: HttpRequest) -> bool:
    return get_and_set_user_agent(request).is_crawler


@register.filter
def is_ai_bot(request: HttpRequest) -> bool:
    return get_and_set_user_agent(request).is_ai_bot


@register.simple_tag
def ai_robots_rules() -> SafeString:
    """Print the robots.txt rules that disallow every AI bot."""
    # robots.txt is plain text, so names must not be HTML-escaped.
    return mark_safe(robots_rules())
