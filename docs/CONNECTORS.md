# Connector contract

Each source connector is optional and independently enabled. A connector must expose:

- `name`: stable platform identifier.
- `capabilities`: search, fetch-by-URL, or parse-user-supplied-content.
- `is_available()`: report whether a compliant access route is configured.
- `search(query, location, date_range)`: return raw records with source URLs and retrieval timestamps.
- `fetch(url)`: retrieve a public/authorized source record when permitted.

## Platform-specific implementation policy

### Xiaohongshu
Use authorized/publicly accessible content, official or licensed interfaces, or content/URLs supplied by the user. Do not evade login, signatures, CAPTCHA, rate limits, or access controls.

### Douyin
Use authorized public endpoints or licensed access where available; support user-provided share URLs and exports. Do not automate account actions or bypass platform controls.

### Dianping
Prefer official/authorized business data and user-provided public listing links. Do not scrape restricted review or merchant data, or bypass anti-bot controls.

### Web
Use a compliant search provider or public pages. Preserve canonical URLs, snippets, publisher, and retrieval time.

If compliant access is not available, return an explicit `unsupported`/unavailable result rather than pretending to search.
