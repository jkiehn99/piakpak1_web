from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AppConfig:
    delay: int = 0
    workers: int = 1
    max_rounds: int = 1
    yolo_path: str = "YOLO5/best.onnx"
    siamese_path: str = "Siamese/IconCompare.onnx"
    v8_js: str = "v8_submit.js"
    result_file: str = "batch_result_protocol.txt"
    proxy_gateway: str = ""
    proxy_rotate: int = 1
    domain: str = "随机"
    blocked_domains: list[str] = field(default_factory=lambda: ["gmeenramy.com"])
    moemail_base_url: str = ""
    moemail_api_key: str = ""
    moemail_default_domain: str = ""
    invite_link: str = ""
    invite_share_id: str = ""
    invite_pass_code_token: str = ""
    invite_trace_file_ids: str = ""
    verbose: bool = False

    @classmethod
    def from_mapping(cls, data: dict[str, Any] | None) -> "AppConfig":
        raw = dict(data or {})
        raw["blocked_domains"] = normalize_list(raw.get("blocked_domains"), default=["gmeenramy.com"])
        raw["domain"] = normalize_domain(raw.get("domain"))
        for key in ("moemail_base_url", "moemail_api_key", "moemail_default_domain"):
            raw[key] = str(raw.get(key, "") or "").strip()
        int_defaults = {"delay": 0, "workers": 1, "max_rounds": 1, "proxy_rotate": 1}
        for key, default in int_defaults.items():
            try:
                raw[key] = int(raw.get(key, default) or default)
            except (TypeError, ValueError):
                raw[key] = default
        raw["verbose"] = bool(raw.get("verbose", False))
        allowed = {f.name for f in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in raw.items() if k in allowed})

    @classmethod
    def load(cls, path: str | Path, defaults: dict[str, Any] | None = None) -> "AppConfig":
        data = dict(defaults or {})
        p = Path(path)
        if p.exists():
            saved = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                data.update(saved)
        return cls.from_mapping(data)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_list(value: Any, default: list[str] | None = None) -> list[str]:
    if value is None or value == "":
        return list(default or [])
    if isinstance(value, str):
        return [x.strip() for x in value.replace("\n", ",").split(",") if x.strip()]
    if isinstance(value, (list, tuple, set)):
        return [str(x).strip() for x in value if str(x).strip()]
    return list(default or [])


def normalize_domain(value: Any) -> str:
    domain = str(value or "随机").strip()
    if domain.startswith("MoeHail"):
        return "MoeHail"
    return domain
