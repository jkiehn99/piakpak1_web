from __future__ import annotations

import re
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import requests


@dataclass
class ProxyTestResult:
    ok: bool
    proxy: str
    ip: str = ""
    elapsed_ms: int = 0
    provider_count: int = 0
    tested_url: str = ""
    error: str = ""
    raw: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = {
            "ok": self.ok,
            "proxy": self.proxy,
            "ip": self.ip,
            "elapsed_ms": self.elapsed_ms,
            "provider_count": self.provider_count,
        }
        if self.tested_url:
            data["tested_url"] = self.tested_url
        if self.error:
            data["error"] = self.error
        if self.raw is not None:
            data["raw"] = self.raw
        return data


class ProxyPool:
    def __init__(self, gateway: str = ""):
        self.gateway = gateway or ""

    @staticmethod
    def split_candidates(proxy_gateway: str) -> list[str]:
        return [p.strip() for p in re.split(r'[\n,;]+', proxy_gateway or "") if p.strip()]

    @staticmethod
    def normalize_url(proxy_url: str) -> str:
        value = (proxy_url or "").strip()
        if not value:
            return value

        scheme = "http"
        rest = value
        if "://" in value:
            scheme, rest = value.split("://", 1)

        if "@" in rest:
            creds, host_part = rest.rsplit("@", 1)
            if ":" in creds:
                username, password = creds.split(":", 1)
                rest = f"{quote(username, safe='')}:{quote(password, safe='')}@{host_part}"
        else:
            parts = rest.split(":")
            if len(parts) >= 4:
                host, port = parts[0], parts[1]
                username = parts[2]
                password = ":".join(parts[3:])
                rest = f"{quote(username, safe='')}:{quote(password, safe='')}@{host}:{port}"

        value = f"{scheme}://{rest}"
        if value.startswith("socks5://") and not value.startswith("socks5h://"):
            value = "socks5h://" + value[len("socks5://"):]
        return value

    def test_first(self, timeout: float = 10.0) -> ProxyTestResult:
        candidates = self.split_candidates(self.gateway)
        if not candidates:
            return ProxyTestResult(ok=False, proxy="", provider_count=0, error="请先填写代理网关或代理池")
        proxy_url = self.normalize_url(candidates[0])
        proxies = {"http": proxy_url, "https": proxy_url}
        test_urls = [
            "https://api.ipify.org?format=json",
            "https://httpbin.org/ip",
            "https://ifconfig.me/all.json",
        ]
        started = time.perf_counter()
        last_error = ""
        for url in test_urls:
            try:
                resp = requests.get(url, proxies=proxies, timeout=timeout)
                elapsed_ms = int((time.perf_counter() - started) * 1000)
                resp.raise_for_status()
                if "json" in resp.headers.get("content-type", ""):
                    data = resp.json()
                else:
                    data = {"ip": resp.text.strip()}
                ip = data.get("ip") or data.get("origin") or data.get("ip_addr") or ""
                return ProxyTestResult(
                    ok=True,
                    proxy=proxy_url,
                    ip=str(ip).split(",")[0].strip(),
                    elapsed_ms=elapsed_ms,
                    provider_count=len(candidates),
                    tested_url=url,
                    raw=data,
                )
            except Exception as exc:
                last_error = str(exc)
        return ProxyTestResult(
            ok=False,
            proxy=proxy_url,
            ip="",
            elapsed_ms=int((time.perf_counter() - started) * 1000),
            provider_count=len(candidates),
            error=last_error,
        )
