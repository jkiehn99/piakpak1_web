"""Maintainability helpers for the PikPak web/GUI wrappers.

This package intentionally starts as a thin layer around the original modules.
The goal is to reduce direct global-state coupling without rewriting the
working registration/captcha flow in one risky step.
"""

from .config import AppConfig
from .mail_provider import MailProvider
from .proxy_pool import ProxyPool, ProxyTestResult
from .result_store import ResultStore
from .state import RuntimeFlags

__all__ = [
    "AppConfig",
    "MailProvider",
    "ProxyPool",
    "ProxyTestResult",
    "ResultStore",
    "RuntimeFlags",
]
