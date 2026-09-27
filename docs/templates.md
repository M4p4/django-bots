# Template tags and filters

## `user_agents` filters

These filters take the request and return a boolean. They have the same names as in
django-user-agents, so existing templates keep working:

```django
{% load user_agents %}

{% if request|is_mobile %}
  <a href="/app/">Get the app</a>
{% endif %}
```

| Filter | Returns |
|---|---|
| `is_mobile` | `request.user_agent.is_mobile` |
| `is_tablet` | `request.user_agent.is_tablet` |
| `is_touch_capable` | `request.user_agent.is_touch_capable` |
| `is_pc` | `request.user_agent.is_pc` |
| `is_bot` | `request.user_agent.is_bot`, which also covers crawlers and AI bots |

The template context needs `request`, which the
`django.template.context_processors.request` context processor adds. The filters use
`request.user_agent` when the middleware has set it, and otherwise parse the header
once and set it on the request. When `request` isn't in the context, every filter
returns `False`.

## `bots` filters

The `bots` library has the `is_crawler` and `is_ai_bot` filters, plus every filter from `user_agents`,
so one `{% load bots %}` is enough:

```django
{% load bots %}

{% if request|is_crawler %}...{% endif %}
{% if request|is_mobile %}...{% endif %}
```

| Filter | Returns |
|---|---|
| `is_crawler` | `request.user_agent.is_crawler` |
| `is_ai_bot` | `request.user_agent.is_ai_bot` |

Like the `user_agents` filters, they need `request` in the context and return `False`
without it.

## Library name clash

Don't keep `django_user_agents` in `INSTALLED_APPS` next to `django_bots`. Both apps
provide a `user_agents` library, and the system check `django_bots.E001` reports the
clash.
