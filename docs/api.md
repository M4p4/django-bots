# API reference

## `django_bots.useragent`

```{eval-rst}
.. automodule:: django_bots.useragent
   :no-index:

.. autofunction:: django_bots.useragent.parse

.. autoclass:: django_bots.useragent.UserAgent
   :members:

.. autoclass:: django_bots.useragent.Browser

.. autoclass:: django_bots.useragent.OperatingSystem

.. autoclass:: django_bots.useragent.Device
```

## `django_bots.crawlers`

```{eval-rst}
.. autofunction:: django_bots.crawlers.is_crawler

.. autofunction:: django_bots.crawlers.crawler_patterns
```

## `django_bots.ai`

```{eval-rst}
.. autofunction:: django_bots.ai.is_ai_bot

.. autofunction:: django_bots.ai.match_ai_bot

.. autofunction:: django_bots.ai.match_ai_bots

.. autofunction:: django_bots.ai.ai_bot_category

.. autofunction:: django_bots.ai.categorize

.. autodata:: django_bots.ai.AI_BOT_CATEGORIES

.. autofunction:: django_bots.ai.ai_bot_names

.. autofunction:: django_bots.ai.ai_bots

.. autofunction:: django_bots.ai.robots_rules
```

## `django_bots`

```{eval-rst}
.. autodata:: django_bots.DATA_VERSIONS
   :no-value:
```

## `django_bots.views`

```{eval-rst}
.. autofunction:: django_bots.views.robots_txt
```

## `django_bots.utils`

```{eval-rst}
.. autofunction:: django_bots.utils.get_user_agent

.. autofunction:: django_bots.utils.get_and_set_user_agent
```

## `django_bots.middleware`

```{eval-rst}
.. autoclass:: django_bots.middleware.UserAgentMiddleware

.. autoclass:: django_bots.middleware.AIBotBlockMiddleware
```
