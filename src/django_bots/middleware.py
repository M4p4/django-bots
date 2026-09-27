"""Middleware that adds ``request.user_agent``."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import cast

from asgiref.sync import iscoroutinefunction, markcoroutinefunction
from django.http import HttpRequest, HttpResponseBase
from django.utils.functional import SimpleLazyObject

from django_bots.utils import get_user_agent

__all__ = ["UserAgentMiddleware"]

GetResponse = Callable[[HttpRequest], HttpResponseBase]
AsyncGetResponse = Callable[[HttpRequest], Awaitable[HttpResponseBase]]


class UserAgentMiddleware:
    """Set ``request.user_agent``, parsed on first access."""

    sync_capable = True
    async_capable = True

    def __init__(self, get_response: GetResponse | AsyncGetResponse) -> None:
        self.get_response = get_response
        self.is_async = iscoroutinefunction(get_response)
        if self.is_async:
            markcoroutinefunction(self)

    def __call__(
        self, request: HttpRequest
    ) -> HttpResponseBase | Awaitable[HttpResponseBase]:
        if self.is_async:
            return self.__acall__(request)
        self.set_user_agent(request)
        return cast(GetResponse, self.get_response)(request)

    async def __acall__(self, request: HttpRequest) -> HttpResponseBase:
        self.set_user_agent(request)
        return await cast(AsyncGetResponse, self.get_response)(request)

    @staticmethod
    def set_user_agent(request: HttpRequest) -> None:
        request.user_agent = SimpleLazyObject(lambda: get_user_agent(request))  # type: ignore[attr-defined]
