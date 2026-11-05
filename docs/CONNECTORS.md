# Connector contract and built-in web search

Each source connector exposes `name`, `is_available()`, and `search(query, location, date_range)`. Connectors must use official APIs, licensed providers, permitted public access, or user-supplied material.

## Built-in Brave Search connector

The `web-search` connector uses the official Brave Search Web endpoint. Configure the API key on the server only:

    export BRAVE_SEARCH_API_KEY="your-key"

The connector sends the key in the `X-Subscription-Token` header and requests structured web results. It maps title, description, URL, and publisher evidence into candidate event records. Search snippets are not event verification: each candidate remains `source_claim` until the event details are corroborated from its primary source.

Install no extra package for this connector; it uses Python's standard library. If the key is missing, source coverage is `unavailable`. Do not put the key in browser code, Git, Skill text, logs, or API responses.

Official API reference: https://api-dashboard.search.brave.com/api-reference/web/search/get

## Platform-specific policy

### Xiaohongshu
Use authorized/publicly accessible content, official or licensed interfaces, or content/URLs supplied by the user. Do not evade login, signatures, CAPTCHA, rate limits, or access controls.

### Douyin
Use authorized public endpoints or licensed access where available; support user-provided share URLs and exports. Do not automate account actions or bypass platform controls.

### Dianping
Prefer official/authorized business data and user-provided public listing links. Do not scrape restricted review or merchant data, or bypass anti-bot controls.

No live Xiaohongshu, Douyin, or Dianping connector is bundled at this release. An absent connector must be reported as unavailable, never simulated.
