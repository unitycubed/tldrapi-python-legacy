# -*- coding: utf-8 -*-
"""Typed exceptions for the TLDRapi legacy Python 2.7 SDK.

Every failure the client raises inherits from `TLDRapiError`. Catch
the base for a safety net, or catch a specific subclass to branch on
failure mode.
"""


class TLDRapiError(Exception):
    """Base for every exception this SDK raises."""

    def __init__(self, message, status_code=None, request_id=None,
                 response_body=None):
        super(TLDRapiError, self).__init__(message)
        self.message = message
        self.status_code = status_code
        self.request_id = request_id
        self.response_body = response_body or {}


class AuthenticationError(TLDRapiError):
    """401/403 — bad or missing X-RapidAPI-Key."""


class InsufficientCreditsError(TLDRapiError):
    """402 — out of credits. Response body carries top-up options."""


class RateLimitError(TLDRapiError):
    """429 — rate limit hit. Honor `retry_after_seconds`."""

    def __init__(self, message, retry_after_seconds=None, **kw):
        super(RateLimitError, self).__init__(message, **kw)
        self.retry_after_seconds = retry_after_seconds


class LanguageNotSupportedError(TLDRapiError):
    """400 with detected non-supported language.

    English-only at launch; cross-lingual is a Month 2-3 feature.
    """


class QualitySelectionRequiresPaidPlanError(TLDRapiError):
    """400 — free-tier customer sent an explicit `tier`. Retry without."""


class InvalidRequestError(TLDRapiError):
    """400 for any other reason."""


class ServerError(TLDRapiError):
    """5xx after the SDK's retries exhausted."""


class NetworkError(TLDRapiError):
    """Transport error — DNS, connection reset, TLS, etc."""


class TimeoutError(TLDRapiError):
    """Request took longer than the client's timeout."""
