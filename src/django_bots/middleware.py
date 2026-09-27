"""Middleware that adds ``request.user_agent`` and blocks AI bots."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, cast

from asgiref.sync import (
    async_to_sync,
    iscoroutinefunction,
    markcoroutinefunction,
    sync_to_async,
)
from django.http import HttpRequest, HttpResponse, HttpResponseBase
from django.template.response import SimpleTemplateResponse
from django.utils.functional import SimpleLazyObject
from django.utils.module_loading import import_string

from django_bots.ai import is_ai_bot
from django_bots.conf import bots_settings
from django_bots.utils import get_user_agent

__all__ = ["AIBotBlockMiddleware", "UserAgentMiddleware"]

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


class AIBotBlockMiddleware:
    """Answer requests from AI bots with ``BOTS_AI_BLOCK_STATUS`` or ``BOTS_AI_BLOCK_VIEW``.

    Only the raw user-agent string is checked, so the user agent is never fully parsed.
    Paths in ``BOTS_AI_BLOCK_EXEMPT_PATHS`` are never blocked.
    """

    sync_capable = True
    async_capable = True

    def __init__(self, get_response: GetResponse | AsyncGetResponse) -> None:
        self.get_response = get_response
        self.is_async = iscoroutinefunction(get_response)
        if self.is_async:
            markcoroutinefunction(self)
        self.block_view = self.load_block_view()

    def load_block_view(self) -> Callable[[HttpRequest], Any] | None:
        path = bots_settings.AI_BLOCK_VIEW
        if path is None:
            return None
        view: Callable[[HttpRequest], Any] = import_string(path)
        # Match the view to the middleware mode, so it can always be called the same way.
        if self.is_async and not iscoroutinefunction(view):
            return sync_to_async(view)
        if not self.is_async and iscoroutinefunction(view):
            return async_to_sync(view)
        return view

    def __call__(
        self, request: HttpRequest
    ) -> HttpResponseBase | Awaitable[HttpResponseBase]:
        if self.is_async:
            return self.__acall__(request)
        if not self.blocks(request):
            return cast(GetResponse, self.get_response)(request)
        if self.block_view is None:
            return self.forbidden()
        response: HttpResponseBase = self.block_view(request)
        # Django only renders template responses returned by the resolved view.
        if isinstance(response, SimpleTemplateResponse):
            response = response.render()
        return response

    async def __acall__(self, request: HttpRequest) -> HttpResponseBase:
        if not self.blocks(request):
            return await cast(AsyncGetResponse, self.get_response)(request)
        if self.block_view is None:
            return self.forbidden()
        response: HttpResponseBase = await self.block_view(request)
        if isinstance(response, SimpleTemplateResponse):
            response = await sync_to_async(response.render)()
        return response

    @staticmethod
    def blocks(request: HttpRequest) -> bool:
        if request.path in bots_settings.AI_BLOCK_EXEMPT_PATHS:
            return False
        return is_ai_bot(request.headers.get("user-agent", ""))

    @staticmethod
    def forbidden() -> HttpResponse:
        return HttpResponse(
            "Forbidden",
            status=bots_settings.AI_BLOCK_STATUS,
            content_type="text/plain; charset=utf-8",
        )
