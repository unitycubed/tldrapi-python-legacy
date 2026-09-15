# -*- coding: utf-8 -*-
"""TLDRapi legacy Python 2.7 SDK.

For modern Python 3.8+ codebases, use the main `tldrapi` package
(https://pypi.org/project/tldrapi/) instead. This `tldrapi-legacy`
package exists ONLY for stuck-on-Python-2.7 environments — CI stuck
on RHEL 6/7, legacy scientific pipelines that cannot yet migrate off
Python 2, embedded systems shipped with 2.7.

Basic use:

    from tldrapi_legacy import TLDRapi
    client = TLDRapi(rapidapi_key="YOUR_RAPIDAPI_KEY")
    result = client.summarize("Long text here...", tier="standard")
    print(result.summary)

"""
from .client import TLDRapi
from .errors import (
    TLDRapiError,
    AuthenticationError,
    InsufficientCreditsError,
    RateLimitError,
    LanguageNotSupportedError,
    QualitySelectionRequiresPaidPlanError,
    ServerError,
    NetworkError,
    TimeoutError,
    InvalidRequestError,
)

__version__ = "0.1.0"
__all__ = [
    "TLDRapi",
    "TLDRapiError",
    "AuthenticationError",
    "InsufficientCreditsError",
    "RateLimitError",
    "LanguageNotSupportedError",
    "QualitySelectionRequiresPaidPlanError",
    "ServerError",
    "NetworkError",
    "TimeoutError",
    "InvalidRequestError",
]
