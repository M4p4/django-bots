from __future__ import annotations

import asyncio

import pytest
from asgiref.sync import iscoroutinefunction
from django.http import HttpRequest, HttpResponse
from django.test import override_settings
from django.utils.functional import SimpleLazyObject

from django_bots import utils
from django_bots.middleware import AIBotBlockMiddleware, UserAgentMiddleware
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


GPTBOT = (
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; "
    "+https://openai.com/gptbot)"
)


def ok_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok")


async def async_ok_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse("ok")


def block_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse("No AI bots", status=451)


async def async_block_view(request: HttpRequest) -> HttpResponse:
    return HttpResponse("No AI bots", status=451)


@pytest.mark.parametrize(
    ("path", "user_agent", "status", "content"),
    [
        ("/", GPTBOT, 403, b"Forbidden"),
        ("/", IPHONE, 200, b"ok"),
        ("/", None, 200, b"ok"),
        ("/robots.txt", GPTBOT, 200, b"ok"),
        ("/robots.txt/", GPTBOT, 403, b"Forbidden"),
    ],
)
def test_block_sync(rf, path, user_agent, status, content):
    middleware = AIBotBlockMiddleware(ok_view)
    headers = {"user-agent": user_agent} if user_agent else {}
    request = rf.get(path, headers=headers)

    response = middleware(request)

    assert not iscoroutinefunction(middleware)
    assert isinstance(response, HttpResponse)
    assert (response.status_code, response.content) == (status, content)


@pytest.mark.parametrize(
    ("user_agent", "status", "content"),
    [(GPTBOT, 403, b"Forbidden"), (IPHONE, 200, b"ok")],
)
def test_block_async(async_rf, user_agent, status, content):
    middleware = AIBotBlockMiddleware(async_ok_view)
    request = async_rf.get("/", headers={"user-agent": user_agent})

    response: HttpResponse = asyncio.run(middleware(request))  # type: ignore[arg-type]

    assert iscoroutinefunction(middleware)
    assert (response.status_code, response.content) == (status, content)


def test_block_default_response(rf):
    middleware = AIBotBlockMiddleware(ok_view)

    with override_settings(BOTS_AI_BLOCK_STATUS=429):
        response = middleware(rf.get("/", headers={"user-agent": GPTBOT}))

    assert isinstance(response, HttpResponse)
    assert response.status_code == 429
    assert response["Content-Type"] == "text/plain; charset=utf-8"


@override_settings(BOTS_AI_ALLOW=["GPTBot"])
def test_block_allow_list(rf):
    middleware = AIBotBlockMiddleware(ok_view)

    response = middleware(rf.get("/", headers={"user-agent": GPTBOT}))

    assert isinstance(response, HttpResponse)
    assert response.status_code == 200


@override_settings(BOTS_AI_BLOCK_EXEMPT_PATHS=["/ai/"])
def test_block_exempt_paths(rf):
    middleware = AIBotBlockMiddleware(ok_view)

    exempt = middleware(rf.get("/ai/", headers={"user-agent": GPTBOT}))
    robots = middleware(rf.get("/robots.txt", headers={"user-agent": GPTBOT}))

    assert isinstance(exempt, HttpResponse)
    assert isinstance(robots, HttpResponse)
    assert (exempt.status_code, robots.status_code) == (200, 403)


@pytest.mark.parametrize("view", ["block_view", "async_block_view"])
def test_block_view_sync(rf, view):
    with override_settings(BOTS_AI_BLOCK_VIEW=f"tests.test_middleware.{view}"):
        middleware = AIBotBlockMiddleware(ok_view)

    response = middleware(rf.get("/", headers={"user-agent": GPTBOT}))

    assert isinstance(response, HttpResponse)
    assert (response.status_code, response.content) == (451, b"No AI bots")


@pytest.mark.parametrize("view", ["block_view", "async_block_view"])
def test_block_view_async(async_rf, view):
    with override_settings(BOTS_AI_BLOCK_VIEW=f"tests.test_middleware.{view}"):
        middleware = AIBotBlockMiddleware(async_ok_view)
    request = async_rf.get("/", headers={"user-agent": GPTBOT})

    response: HttpResponse = asyncio.run(middleware(request))  # type: ignore[arg-type]

    assert (response.status_code, response.content) == (451, b"No AI bots")
