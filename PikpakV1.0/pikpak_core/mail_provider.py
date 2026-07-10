from __future__ import annotations

from typing import Callable

import lib.mail


class MailProvider:
    """Thin adapter over the existing lib.mail module.

    This keeps the current behavior unchanged while giving future GUI/Web code a
    provider-shaped seam for mock, IMAP, or user-supplied custom API providers.
    """

    def __init__(
        self,
        force_domain: str | None = None,
        blocked_domains: list[str] | None = None,
        moemail_base_url: str | None = None,
        moemail_api_key: str | None = None,
        moemail_default_domain: str | None = None,
    ):
        self.force_domain = None if not force_domain or force_domain == "随机" else force_domain
        self.blocked_domains = set(blocked_domains or []) | {"gmeenramy.com"}
        self.moemail_base_url = (moemail_base_url or "").strip()
        self.moemail_api_key = (moemail_api_key or "").strip()
        self.moemail_default_domain = (moemail_default_domain or "").strip()

    def apply_globals(self) -> None:
        lib.mail._FORCE_DOMAIN = self.force_domain
        lib.mail._BLOCKED_DOMAINS = set(self.blocked_domains)
        lib.mail.configure_moemail(
            base_url=self.moemail_base_url,
            api_key=self.moemail_api_key,
            default_domain=self.moemail_default_domain,
        )

    def create_account(self):
        self.apply_globals()
        return lib.mail.create_mail_account(force_domain=self.force_domain)

    def fetch_code(self, email: str, token: str, base_url: str | None = None, provider_type: str | None = None, stop_check: Callable | None = None):
        return lib.mail.fetch_verification_code(email, token, base_url, stop_check=stop_check, provider_type=provider_type)

    def available_domains(self) -> list[str]:
        self.apply_globals()
        return lib.mail.get_available_domains()
