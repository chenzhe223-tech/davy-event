# Connector contract and built-in web search

Each source connector exposes `name`, `is_available()`, and `search(query, location, date_range)`. Connectors must use official APIs, licensed providers, permitted public access, or user-supplied material.

## Default: Volcengine Doubao Global Search

The `web-search` connector uses the official Global Search API:

- Endpoint: `https://open.feedcoopapi.com/search_api/global_search`
- Method: POST
- Authentication: `Authorization: Bearer <API_KEY>`
- Environment variable: `VOLCENGINE_SEARCH_API_KEY`
- Request fields: `Query`, `SearchType=web`, `DocCount`, `MaxSnippetLength`

Configure the key only in the server environment:

    $env:VOLCENGINE_SEARCH_API_KEY = "your-key"

The provider currently documents 500 free searches per Volcengine account per month, shared by Global and Custom editions. The quota is consumed before paid usage. This project does not automatically switch to another provider or enable paid fallback when the quota is exhausted. A quota error is reported as a connector error so the user can stop and decide.

Search titles, URLs, snippets, publisher metadata, and publish-time hints are mapped into candidate records. Search results remain `source_claim`; they are not proof that an event is current or accurate. The API key must never be placed in browser code, Git, Skill text, logs, or API responses.

Official references:
- https://docs.volcengine.com/docs/networked-search/doubao-search-global-edition?lang=zh
- https://docs.volcengine.com/docs/networked-search/networked-search?lang=zh

## Optional legacy Brave connector

The `BraveSearchConnector` class remains available for users who explicitly choose to configure it, but it is no longer registered as the default provider.

## Platform-specific policy

### Xiaohongshu
Use authorized/publicly accessible content, official or licensed interfaces, or content/URLs supplied by the user. Do not evade login, signatures, CAPTCHA, rate limits, or access controls.

### Douyin
Use authorized public endpoints or licensed access where available; support user-provided share URLs and exports. Do not automate account actions or bypass platform controls.

### Dianping
Prefer official/authorized business data and user-provided public listing links. Do not scrape restricted review or merchant data, or bypass anti-bot controls.

No live Xiaohongshu, Douyin, or Dianping connector is bundled at this release. An absent connector must be reported as unavailable, never simulated.
