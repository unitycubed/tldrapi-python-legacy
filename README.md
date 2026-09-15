# tldrapi-legacy — Python 2.7 SDK for TLDRapi

Legacy Python 2.7 client for [TLDRapi](https://tldrapi.com) — turn any
content into a clean summary in one API call.

> **⚠️ Use the modern SDK if you can.** For Python 3.8+ codebases, use
> [`tldrapi`](https://pypi.org/project/tldrapi/) instead — it has
> native async, typed hints, richer error hierarchy, and richer
> features. `tldrapi-legacy` exists ONLY for stuck-on-Python-2.7
> environments — CI/scientific pipelines on RHEL 6/7 that cannot yet
> migrate, embedded systems shipped with 2.7, third-party build
> systems that pinned an ancient interpreter.

- **Free tier** — 100 credits per month, no card, no trial expiry
- **Sync-only** — no `asyncio` (2.7 doesn't have it)
- **One runtime dep**: `requests` (the only viable HTTP lib that still
  supports 2.7 out of the box)
- **Same public API surface** as the modern SDK where the shape
  permits (typed exceptions, `SummarizeResult`, `usage()`, `rates()`)

## Install

```bash
pip install tldrapi-legacy
# or, on systems with both Python 2 and 3:
pip2 install tldrapi-legacy
```

Python 2.7 or Python 3.4–3.7. Modern Python (3.8+) users should
install [`tldrapi`](https://pypi.org/project/tldrapi/) instead.

## Getting your free key

1. Sign in at [rapidapi.com](https://rapidapi.com)
2. Subscribe to the [TLDRapi Summarizer](https://rapidapi.com/thunderAPIs256/api/tldrapi-summarizer)
   listing — choose **BASIC (Free)**
3. Open the listing → **Console** → **Applications** → **Add App**
4. In the App → **Authorizations** tab → copy the Authorization Key

Pass it to `TLDRapi(rapidapi_key=...)`. Everything on the free tier
works exactly like the paid tiers — same endpoints, same response
shape, same SDK — just with a 100-credit monthly cap.

## Hello world

```python
from tldrapi_legacy import TLDRapi

client = TLDRapi(rapidapi_key="YOUR_RAPIDAPI_KEY")
result = client.summarize("Some long article body here...")
print(result.summary)
print("credits remaining: %s" % result.credits.get("remaining"))
```

## Examples

### Summarize with a specific quality tier

```python
result = client.summarize(long_text, tier="deep")
```

Available tiers: `quick`, `standard`, `deep`, `premium`, `ultra`, or
any of the 25 compound presets like `"thorough-standard"`. Full
pricing detail (methodology, formula, dynamic-pricing audit trail):
[tldrapi.com/pricing](https://tldrapi.com/pricing).

### Summarize an article by URL

```python
result = client.summarize("https://arxiv.org/abs/1706.03762",
                          tier="deep")
print(result.summary)
```

### Session pinning across a batch

```python
r1 = client.summarize("Doc 1")
r2 = client.summarize("Doc 2", session_id=r1.session_id)
r3 = client.summarize("Doc 3", session_id=r1.session_id)
```

### Handle a rate-limit with backoff

```python
import time
from tldrapi_legacy import RateLimitError

for attempt in range(3):
    try:
        r = client.summarize(text, tier="deep")
        print(r.summary)
        break
    except RateLimitError as e:
        time.sleep(e.retry_after_seconds or 60)
```

### Show live credit balance to your user

```python
u = client.usage()
print("You have %d credits left (%s)" % (u.credits_remaining, u.plan))

r = client.summarize(text)
print("That call cost %s credits. Remaining: %s" %
      (r.credits.get("charged"), r.credits.get("remaining")))
```

### Advanced quality controls — 3 axes, 30 named presets

```python
# named preset
r = client.summarize(text, tier="thorough-quick")

# preset + one axis override (axes win, server returns X-Quality-Warning)
r = client.summarize(text, tier="premium",
                     optional_extractive_lvl="brief")

# all three axes, no preset
r = client.summarize(text,
                     optional_quality="ultra",
                     optional_extractive_lvl="complete",
                     optional_strategy="premium-single-shot")

# opt into permissive downgrade on paid-tier
r = client.summarize(text, tier="premium", allow_downgrade=True)
```

## Error handling

```python
from tldrapi_legacy import (
    TLDRapiError, AuthenticationError, InsufficientCreditsError,
    RateLimitError, LanguageNotSupportedError,
    QualitySelectionRequiresPaidPlanError, ServerError, TimeoutError,
)

try:
    r = client.summarize(user_text, tier="deep")
except InsufficientCreditsError as e:
    top_up = e.response_body.get("options", {}).get("top_up", {}).get("url")
    # …prompt the user to top up…
except RateLimitError as e:
    time.sleep(e.retry_after_seconds or 60)
except LanguageNotSupportedError:
    # English-only at launch
    pass
except QualitySelectionRequiresPaidPlanError:
    # Free plan can't pick tier; retry without it
    r = client.summarize(user_text)
except TimeoutError:
    r = client.summarize(user_text, tier="deep", timeout=120)
except TLDRapiError as e:
    print("TLDRapi error %s (req %s): %s" %
          (e.status_code, e.request_id, e))
```

Every error carries `.status_code`, `.request_id` (attach when
reporting bugs), and `.response_body`.

## Configuration

```python
client = TLDRapi(
    rapidapi_key="YOUR_KEY",
    rapidapi_host="tldrapi-summarizer.p.rapidapi.com",  # staging override
    base_url=None,                       # default = https://{rapidapi_host}
    timeout=60.0,                        # per-request seconds
    retries=3,                           # 5xx + network only
)
```

## What's missing vs the modern SDK

The modern `tldrapi` (Python 3.8+) supports these features that
`tldrapi-legacy` deliberately omits because Python 2.7 can't do them
well or at all:

- Async client (`AsyncTLDRapi`) — no `asyncio` in Python 2.7
- Native `submit_async` / `wait_for_result` helpers (reachable today
  via manual GET polling of `/paid/result/{id}`)
- Multipart file-upload helpers for the `/convert/*` binary endpoints
  (still callable via raw `requests.post` if needed)
- Custom-prompt management helpers
- Type-hinted API surface

If you need any of those, migrating a single service to Python 3.8+
gets you the modern SDK. The wire protocol is identical.

## License

Released under the MIT License — see [LICENSE](LICENSE).

Copyright (c) 2026 Ehren Biglari / Unity Cubed.
