# Limits

django-bots looks at the `User-Agent` header and nothing else. Keep these limits in
mind when you rely on it.

## User agents can be faked

Any client can send any user agent. A scraper can claim to be Chrome, and a script can
claim to be Googlebot. Detection catches clients that identify themselves honestly,
which most large crawlers and AI bots do. It doesn't catch clients that hide.

django-bots doesn't check IP addresses or reverse DNS, so it can't tell a real
Googlebot from a fake one.

## Browsers send less detail

Chrome and other Chromium browsers send a reduced user agent: the minor version is
always `0.0.0`, and on Android the device model is always `K`. Version numbers and
device models from these browsers are less precise than they used to be. The
User-Agent Client Hints headers carry the full detail, and django-bots doesn't read
them.

## Long user agents

Only the first 512 characters of a user agent are parsed and matched. Real user agents
are well under that, and the limit keeps the work per request small whatever a client
sends. A bot name that appears only after the first 512 characters isn't detected.
`request.user_agent.ua_string` still holds the full header.

## Devices that hide their type

Safari on iPadOS 13 and later sends the same user agent as Safari on a Mac, so an iPad
is `is_pc` and not `is_tablet`. The user agent has nothing to tell them apart. Smart TVs
and game consoles are none of `is_mobile`, `is_tablet`, `is_pc` or `is_bot`.

## robots.txt is voluntary

robots.txt rules are a request, not a barrier. Well-behaved crawlers follow them, and
others ignore them. ai.robots.txt records, where known, whether each bot respects
robots.txt, in the `respect` field of `django_bots.ai.ai_bots()`.

## Caches in front of Django

`AIBotBlockMiddleware` only sees requests that reach Django. A CDN or reverse proxy
that caches pages serves them to AI bots from the cache, and it may also cache the
block response and serve it to other visitors. Block AI bots at the cache as well. The
default block response sends `Cache-Control: private, no-store` to keep itself out of
shared caches; a view in `BOTS_AI_BLOCK_VIEW` should do the same.

## Broad entries

ai.robots.txt lists some bots that you may not think of as AI bots, and a few names
that are ordinary words:

- `facebookexternalhit` builds link previews on Facebook, Messenger and WhatsApp.
- `Applebot` powers search in Siri and Spotlight, not only Apple's AI features. Apple's
  AI training opt-out is the separate `Applebot-Extended` token.
- `PetalBot` is the crawler of Huawei's Petal Search, and `GoogleOther` does Google's
  research and one-off crawls.
- `Code`, `Cursor` and `Trae` also appear in the user agents of the VS Code, Cursor and
  Trae desktop apps, so people opening your site in their built-in browsers match.
  They're [agents](ai-bots.md#categories), which the middleware doesn't block by
  default.
- `Spider` matches any user agent with `spider` as a separate word, such as the Sogou
  search crawler and Screaming Frog SEO Spider.

If one of them matters for your site, add it to `BOTS_AI_ALLOW`.

## Lists change

Both data sources are updated often. A bot that appeared last week may not be in the
bundled ai.robots.txt release or the installed crawler-user-agents version yet. Use
`BOTS_AI_EXTRA` and `BOTS_CRAWLER_EXTRA` to cover the gap.
