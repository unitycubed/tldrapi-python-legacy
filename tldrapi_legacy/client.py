# -*- coding: utf-8 -*-
"""TLDRapi legacy Python 2.7 client.

Sync-only client for stuck-on-Python-2.7 environments. Uses `requests`
(the only viable HTTP lib that still supports 2.7). For modern Python
3.8+ codebases use the `tldrapi` package instead — it has native
async, typed hints, and much richer error hierarchy.
"""
from __future__ import print_function

import json
import random
import time

import requests

from .errors import (
    AuthenticationError,
    InsufficientCreditsError,
    InvalidRequestError,
    LanguageNotSupportedError,
    NetworkError,
    QualitySelectionRequiresPaidPlanError,
    RateLimitError,
    ServerError,
    TimeoutError,
    TLDRapiError,
)

DEFAULT_HOST = "tldrapi-summarizer.p.rapidapi.com"
DEFAULT_TIMEOUT = 60.0
DEFAULT_RETRIES = 3

VALID_TIERS = ("quick", "standard", "deep", "premium", "ultra")


class SummarizeResult(object):
    """Return of `client.summarize(...)`.

    Attributes:
      summary: str — the summarized text
      session_id: str — pin future calls with `session_id=` to reuse model
      request_id: str — X-Request-ID; attach when reporting an issue
      usage: dict — {input_tokens, output_tokens, total_cost, model_used}
      credits: dict — {charged, remaining, tier} snapshot
      raw: dict — full parsed body, anything not hoisted onto typed fields
    """
    __slots__ = ("summary", "session_id", "request_id", "usage",
                 "credits", "raw")

    def __init__(self, summary, session_id, request_id, usage, credits, raw):
        self.summary = summary
        self.session_id = session_id
        self.request_id = request_id
        self.usage = usage
        self.credits = credits
        self.raw = raw


class UsageStats(object):
    __slots__ = ("usage_count", "successful_requests", "failed_requests",
                 "plan", "credits_remaining", "raw")

    def __init__(self, raw):
        self.raw = raw
        self.usage_count = raw.get("usage_count", 0)
        self.successful_requests = raw.get("successful_requests", 0)
        self.failed_requests = raw.get("failed_requests", 0)
        self.plan = raw.get("plan", "free")
        limits = raw.get("limits") or {}
        self.credits_remaining = limits.get("credits", 0)


class Rates(object):
    __slots__ = ("raw", "quick", "standard", "deep", "premium", "ultra")

    def __init__(self, raw):
        self.raw = raw
        tiers = raw.get("tiers") or raw.get("rates") or []
        by_name = {}
        for t in tiers:
            name = t.get("tier") or t.get("name") or t.get("quality")
            if name:
                by_name[name] = t
        self.quick = by_name.get("quick")
        self.standard = by_name.get("standard")
        self.deep = by_name.get("deep")
        self.premium = by_name.get("premium")
        self.ultra = by_name.get("ultra")


class TLDRapi(object):
    """Synchronous TLDRapi client for Python 2.7.

    Basic usage:

        from tldrapi_legacy import TLDRapi
        client = TLDRapi(rapidapi_key="YOUR_KEY")
        result = client.summarize("Long text...", tier="standard")
        print(result.summary)
    """

    def __init__(self, rapidapi_key, rapidapi_host=None, base_url=None,
                 timeout=None, retries=None):
        if not rapidapi_key:
            raise ValueError("rapidapi_key is required")
        self.rapidapi_key = rapidapi_key
        self.rapidapi_host = rapidapi_host or DEFAULT_HOST
        self.base_url = base_url or ("https://" + self.rapidapi_host)
        self.timeout = float(timeout) if timeout is not None else DEFAULT_TIMEOUT
        self.retries = int(retries) if retries is not None else DEFAULT_RETRIES
        self._session = requests.Session()

    # ---------------- summarize ----------------

    def summarize(self, input_text, tier=None, session_id=None,
                  model_alias=None, allow_overage=False,
                  allow_downgrade=False, optional_quality=None,
                  optional_extractive_lvl=None, optional_strategy=None,
                  extra_headers=None, timeout=None):
        """POST /summarize.

        Args:
          input_text: str or URL — the content to summarize
          tier: one of the 30 named presets (quick/standard/deep/premium/
            ultra, or a compound like 'thorough-standard'); None → server default
          session_id: pin to a previous SummarizeResult.session_id
          model_alias: force a specific model (rarely needed)
          allow_overage: pay 2x rate rather than 402 when balance is low
          allow_downgrade: opt-in permissive paid-tier fallback
          optional_quality: LLM axis override (quick/standard/deep/premium/ultra)
          optional_extractive_lvl: retention axis
            (minimal/brief/balanced/thorough/detailed/complete)
          optional_strategy: inference strategy
            (contextual-compression/premium-single-shot/hierarchical-merge)
          extra_headers: dict of extra HTTP headers to include
          timeout: per-call timeout override, seconds
        """
        body = {"input_text": input_text}
        if session_id:
            body["session_id"] = session_id
        if model_alias:
            body["config"] = {"model_alias": model_alias}

        headers = {"Content-Type": "application/json"}
        if tier:
            headers["X-Quality"] = tier
        if allow_overage:
            headers["X-Allow-Overage"] = "true"
        if allow_downgrade:
            headers["X-Allow-Downgrade"] = "true"
        if optional_quality:
            headers["X-Optional-Quality"] = optional_quality
        if optional_extractive_lvl:
            headers["X-Optional-Extractive-Lvl"] = optional_extractive_lvl
        if optional_strategy:
            headers["X-Optional-Strategy"] = optional_strategy
        if extra_headers:
            for k, v in extra_headers.items():
                headers[k] = v

        response_body, response_headers = self._request(
            "POST", "/summarize",
            data=json.dumps(body).encode("utf-8"),
            headers=headers, timeout=timeout,
        )

        return SummarizeResult(
            summary=response_body.get("summary", ""),
            session_id=response_body.get("session_id",
                                          response_headers.get("X-Session-ID", "")),
            request_id=response_headers.get("X-Request-ID", ""),
            usage=response_body.get("usage") or {},
            credits=self._extract_credits(response_headers),
            raw=response_body,
        )

    # ---------------- rates / usage ----------------

    def rates(self):
        body, _headers = self._request("GET", "/rates")
        return Rates(body)

    def usage(self):
        body, _headers = self._request("GET", "/usage")
        return UsageStats(body)

    # ---------------- internals ----------------

    def _extract_credits(self, headers):
        return {
            "charged": headers.get("X-Credits-Charged"),
            "remaining": headers.get("X-Credits-Remaining"),
            "tier": headers.get("X-Credits-Tier"),
        }

    def _request(self, method, path, data=None, headers=None, timeout=None):
        h = {
            "X-RapidAPI-Key": self.rapidapi_key,
            "X-RapidAPI-Host": self.rapidapi_host,
            "Accept": "application/json",
            "User-Agent": "tldrapi-legacy-python/0.1.0",
        }
        if headers:
            for k, v in headers.items():
                h[k] = v

        url = self.base_url + path
        eff_timeout = float(timeout) if timeout is not None else self.timeout
        last_exc = None

        for attempt in range(0, max(1, self.retries + 1)):
            try:
                resp = self._session.request(
                    method, url, data=data, headers=h, timeout=eff_timeout,
                )
            except requests.exceptions.Timeout as e:
                last_exc = TimeoutError(
                    "request timed out after {0}s".format(eff_timeout))
                if attempt < self.retries:
                    self._sleep_backoff(attempt)
                    continue
                raise last_exc
            except requests.exceptions.RequestException as e:
                last_exc = NetworkError(
                    "transport error: {0}".format(str(e)))
                if attempt < self.retries:
                    self._sleep_backoff(attempt)
                    continue
                raise last_exc

            body, parsed = self._parse_body(resp)
            if 200 <= resp.status_code < 300:
                return body, resp.headers

            # error mapping
            req_id = resp.headers.get("X-Request-ID", "")
            msg = self._error_message(parsed, resp.status_code)

            if resp.status_code == 401 or resp.status_code == 403:
                raise AuthenticationError(msg, status_code=resp.status_code,
                                          request_id=req_id, response_body=parsed)
            if resp.status_code == 402:
                raise InsufficientCreditsError(
                    msg, status_code=resp.status_code, request_id=req_id,
                    response_body=parsed)
            if resp.status_code == 429:
                retry_after = self._parse_retry_after(resp.headers.get("Retry-After"))
                raise RateLimitError(
                    msg, retry_after_seconds=retry_after,
                    status_code=resp.status_code, request_id=req_id,
                    response_body=parsed)
            if resp.status_code == 400:
                error_type = parsed.get("error_type") or parsed.get("error", {}).get("type")
                if error_type == "language_not_supported":
                    raise LanguageNotSupportedError(
                        msg, status_code=400, request_id=req_id,
                        response_body=parsed)
                if error_type == "quality_selection_requires_paid_plan":
                    raise QualitySelectionRequiresPaidPlanError(
                        msg, status_code=400, request_id=req_id,
                        response_body=parsed)
                raise InvalidRequestError(
                    msg, status_code=400, request_id=req_id,
                    response_body=parsed)
            if resp.status_code >= 500:
                if attempt < self.retries:
                    self._sleep_backoff(attempt)
                    continue
                raise ServerError(msg, status_code=resp.status_code,
                                  request_id=req_id, response_body=parsed)

            raise TLDRapiError(msg, status_code=resp.status_code,
                               request_id=req_id, response_body=parsed)

        if last_exc:
            raise last_exc
        raise TLDRapiError("request failed after retries")

    def _parse_body(self, resp):
        try:
            parsed = resp.json()
            return parsed, parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}, {"raw_text": resp.text}

    def _error_message(self, parsed, status_code):
        if isinstance(parsed, dict):
            for k in ("message", "error_message", "detail"):
                v = parsed.get(k)
                if v:
                    return str(v)
            err = parsed.get("error")
            if isinstance(err, dict):
                v = err.get("message") or err.get("detail")
                if v:
                    return str(v)
        return "HTTP {0}".format(status_code)

    def _parse_retry_after(self, v):
        if not v:
            return None
        try:
            return int(float(v))
        except (TypeError, ValueError):
            return None

    def _sleep_backoff(self, attempt):
        # exponential + jitter, capped at 30s
        base = min(30.0, (2 ** attempt) * 0.5)
        time.sleep(base + random.random() * 0.5)

    def close(self):
        self._session.close()

    # context manager support
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
