"""Template filters with the same names as django-user-agents' ``user_agents`` library."""

from __future__ import annotations

from django import template
from django.http import HttpRequest

from django_bots.utils import get_and_set_user_agent

register = template.Library()


@register.filter
def is_mobile(request: HttpRequest) -> bool:
    return get_and_set_user_agent(request).is_mobile


@register.filter
def is_tablet(request: HttpRequest) -> bool:
    return get_and_set_user_agent(request).is_tablet


@register.filter
def is_touch_capable(request: HttpRequest) -> bool:
    return get_and_set_user_agent(request).is_touch_capable


@register.filter
def is_pc(request: HttpRequest) -> bool:
    return get_and_set_user_agent(request).is_pc


@register.filter
def is_bot(request: HttpRequest) -> bool:
    return get_and_set_user_agent(request).is_bot
