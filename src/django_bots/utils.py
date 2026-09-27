"""Helpers to get the parsed user agent of a request."""

from __future__ import annotations

from typing import overload

from django.http import HttpRequest

from django_bots.useragent import UserAgent, parse

__all__ = ["get_and_set_user_agent", "get_user_agent"]


@overload
def get_user_agent(request: HttpRequest) -> UserAgent: ...
@overload
def get_user_agent(request: object) -> UserAgent | str: ...
def get_user_agent(request: object) -> UserAgent | str:
    """Parse the request's user agent. An object without ``META`` gives ``''``."""
    meta = getattr(request, "META", None)
    if meta is None:
        return ""
    return parse(meta.get("HTTP_USER_AGENT", ""))


@overload
def get_and_set_user_agent(request: HttpRequest) -> UserAgent: ...
@overload
def get_and_set_user_agent(request: object) -> UserAgent | str: ...
def get_and_set_user_agent(request: object) -> UserAgent | str:
    """Return ``request.user_agent``, parsing and setting it first if it's missing."""
    if hasattr(request, "user_agent"):
        existing: UserAgent = request.user_agent
        return existing
    if not request:
        return parse("")
    user_agent = get_user_agent(request)
    setattr(request, "user_agent", user_agent)  # noqa: B010
    return user_agent
