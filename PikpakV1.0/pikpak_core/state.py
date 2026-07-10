from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class RuntimeFlags:
    """Small shared runtime state holder for wrappers.

    The original main.py still owns its global stop event. This class gives GUI/Web
    code a named place for wrapper-local cancellation and callbacks while the
    larger TaskRunner extraction is deferred.
    """

    stop_event: threading.Event = field(default_factory=threading.Event)
    worker_tls: threading.local = field(default_factory=threading.local)
    captcha_callback: Callable | None = None

    def stop(self) -> None:
        self.stop_event.set()

    def clear(self) -> None:
        self.stop_event.clear()

    def stopped(self) -> bool:
        return self.stop_event.is_set()

    def set_worker_id(self, worker_id: int | None) -> None:
        self.worker_tls.wid = worker_id

    def get_worker_id(self) -> int | None:
        return getattr(self.worker_tls, "wid", None)
