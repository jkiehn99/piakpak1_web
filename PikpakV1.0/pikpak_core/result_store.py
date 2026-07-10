from __future__ import annotations

import threading
import time
from pathlib import Path

RESULT_SEPARATOR = "----"


def split_result_line(line: str) -> list[str]:
    separator = RESULT_SEPARATOR if RESULT_SEPARATOR in line else "|"
    return [p.strip() for p in line.split(separator)]


def join_result_fields(fields: list[str]) -> str:
    return f" {RESULT_SEPARATOR} ".join(fields)


class ResultStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.lock = threading.Lock()

    def append(self, email: str, password: str, access_token: str = "", user_id: str = "", invite_ok=None, pro_ok=None, refresh_token: str = "", captcha_token: str = "", device_id: str = "") -> dict[str, str]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        reg_time = time.strftime("%Y-%m-%d %H:%M:%S")
        invite_str = "" if invite_ok is None else ("成功" if invite_ok else "失败")
        pro_str = "" if pro_ok is None else ("成功" if pro_ok else "失败")
        line = join_result_fields([email, password, access_token, refresh_token, user_id, reg_time, invite_str, pro_str, captcha_token, device_id]) + "\n"
        with self.lock:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line)
        return {
            "email": email,
            "password": password,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_id": user_id,
            "reg_time": reg_time,
            "invite": invite_str,
            "pro": pro_str,
            "captcha_token": captcha_token,
            "device_id": device_id,
        }

    def read_accounts(self) -> list[dict[str, str]]:
        if not self.path.exists():
            return []
        accounts: list[dict[str, str]] = []
        for line in self.path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip() or ("邮箱" in line and "密码" in line):
                continue
            parts = split_result_line(line)
            if len(parts) >= 8:
                accounts.append({
                    "email": parts[0],
                    "password": parts[1],
                    "access_token": parts[2],
                    "refresh_token": parts[3],
                    "user_id": parts[4],
                    "reg_time": parts[5],
                    "invite": parts[6],
                    "pro": parts[7],
                    "captcha_token": parts[8] if len(parts) >= 9 else "",
                    "device_id": parts[9] if len(parts) >= 10 else "",
                })
            elif len(parts) >= 6:
                accounts.append({
                    "email": parts[0],
                    "password": parts[1],
                    "access_token": parts[2],
                    "refresh_token": "",
                    "user_id": parts[3],
                    "reg_time": parts[4],
                    "invite": parts[5],
                    "pro": parts[6] if len(parts) >= 7 else "",
                    "captcha_token": "",
                    "device_id": "",
                })
        return accounts
