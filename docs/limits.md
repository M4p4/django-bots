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

## robots.txt is voluntary

robots.txt rules are a request, not a barrier. Well-behaved crawlers follow them, and
others ignore them. ai.robots.txt records, where known, whether each bot respects
robots.txt, in the `respect` field of `django_bots.ai.ai_bots()`.

## Broad entries

ai.robots.txt lists some bots that you may not think of as AI bots, and a few names
that are ordinary words:

- `facebookexternalhit` builds link previews on Facebook, Messenger and WhatsApp.
- `Applebot` powers search in Siri and Spotlight, not only Apple's AI features. Apple's
  AI training opt-out is the separate `Applebot-Extended` token.
- `Code` also appears in the user agent of the Visual Studio Code desktop app, for
  example in its built-in browser.
- `Spider` matches any user agent with `spider` as a separate word.

If one of them matters for your site, add it to `BOTS_AI_ALLOW`.

## Lists change

Both data sources are updated often. A bot that appeared last week may not be in the
bundled ai.robots.txt release or the installed crawler-user-agents version yet. Use
`BOTS_AI_EXTRA` and `BOTS_CRAWLER_EXTRA` to cover the gap.
