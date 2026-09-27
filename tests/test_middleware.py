from __future__ import annotations

import asyncio

from asgiref.sync import iscoroutinefunction
from django.http import HttpRequest, HttpResponse
from django.utils.functional import SimpleLazyObject

from django_bots import utils
from django_bots.middleware import UserAgentMiddleware
from django_bots.useragent import parse as real_parse

IPHONE = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 5_1 like Mac OS X) AppleWebKit/534.46 "
    "(KHTML, like Gecko) Version/5.1 Mobile/9B179 Safari/7534.48.3"
)


def sync_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse(str(request.user_agent))  # type: ignore[attr-defined]


async def async_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse(str(request.user_agent))  # type: ignore[attr-defined]


def test_sync_sets_user_agent(rf):
    middleware = UserAgentMiddleware(sync_view)
    request = rf.get("/", HTTP_USER_AGENT=IPHONE)

    response = middleware(request)

    assert not iscoroutinefunction(middleware)
    assert isinstance(response, HttpResponse)
    assert response.content == b"iPhone / iOS 5.1 / Mobile Safari 5.1"


def test_async_sets_user_agent(async_rf):
    middleware = UserAgentMiddleware(async_view)
    request = async_rf.get("/", headers={"user-agent": IPHONE})

    response: HttpResponse = asyncio.run(middleware(request))  # type: ignore[arg-type]

    assert iscoroutinefunction(middleware)
    assert response.content == b"iPhone / iOS 5.1 / Mobile Safari 5.1"


def test_parses_lazily(monkeypatch, rf):
    calls = []

    def spy(ua_string):
        calls.append(ua_string)
        return real_parse(ua_string)

    monkeypatch.setattr(utils, "parse", spy)
    request = rf.get("/", HTTP_USER_AGENT=IPHONE)
    UserAgentMiddleware(lambda request: HttpResponse())(request)

    assert isinstance(request.user_agent, SimpleLazyObject)
    assert calls == []
    assert request.user_agent.is_mobile
    assert request.user_agent.is_tablet is False
    assert calls == [IPHONE]
