"""Template filters with the same names as django-user-agents' ``user_agents`` library."""

from __future__ import annotations

from django import template
from django.http import HttpRequest

from django_bots.useragent import UserAgent, parse
from django_bots.utils import get_and_set_user_agent

register = template.Library()


def request_user_agent(request: object) -> UserAgent:
    """Return the request's user agent, or an empty one for anything that isn't a request."""
    if not hasattr(request, "user_agent") and not hasattr(request, "META"):
        return parse("")
    user_agent = get_and_set_user_agent(request)
    return user_agent if isinstance(user_agent, UserAgent) else parse("")


@register.filter
def is_mobile(request: HttpRequest) -> bool:
    return request_user_agent(request).is_mobile


@register.filter
def is_tablet(request: HttpRequest) -> bool:
    return request_user_agent(request).is_tablet


@register.filter
def is_touch_capable(request: HttpRequest) -> bool:
    return request_user_agent(request).is_touch_capable


@register.filter
def is_pc(request: HttpRequest) -> bool:
    return request_user_agent(request).is_pc


@register.filter
def is_bot(request: HttpRequest) -> bool:
    return request_user_agent(request).is_bot
