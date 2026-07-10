import os
import random
import re
import string
import time

from .http_client import make_request

_MAILTM_URL = "https://api.mail.tm"

_TEMPMĀILIO_URL = "https://api.internal.temp-mail.io"
_TEMPMĀILIO_DOMAINS_CACHE = None
_TEMPMĀILIO_DOMAINS_CACHE_TIME = 0

_TEMPMĀILLOL_URL = "https://api.tempmail.lol"
_TEMPMĀILLOL_DOMAINS_CACHE = None
_TEMPMĀILLOL_DOMAINS_CACHE_TIME = 0

_GPTMAIL_URL = "https://mail.chatgpt.org.uk"
_GPTMAIL_POOL_LABEL = "GPTMail随机池"
_MOEMAIL_URL = ""
_MOEMAIL_API_KEY = ""
_MOEMAIL_DEFAULT_DOMAIN = ""
_MOEMAIL_POOL_LABEL = "MoeHail"
_MOEMAIL_EXPIRY_TIME = 3600000
_MOEMAIL_POLL_INTERVAL = 5
_MOEMAIL_MAX_POLL_TIMES = 24
_FORCE_DOMAIN = None
_BLOCKED_DOMAINS = {"gmeenramy.com"}

_MOEMAIL_ENV_URL = "MOEMAIL_BASE_URL"
_MOEMAIL_ENV_API_KEY = "MOEMAIL_API_KEY"
_MOEMAIL_ENV_DEFAULT_DOMAIN = "MOEMAIL_DEFAULT_DOMAIN"

_FALLBACK_DOMAINS = [
    "oakon.com", "teihu.com", "raleigh-construction.com",
    "pastryofistanbul.com", "questtechsystems.com",
]


_FOREIGN_NAME_PREFIXES = [
    "adriancole", "alexandergray", "ameliahayes", "annabrooks", "anthonyward",
    "arianafoster", "aubreyjames", "benjaminclark", "carterlewis", "charlottejones",
    "chloeadams", "christopherhall", "danielwalker", "davidhughes", "eleanormorris",
    "elijahyoung", "ellawright", "emilyscott", "ethanprice", "evansanders",
    "gabrielross", "gracebennett", "hannahcooper", "hazelmurphy", "henrywatson",
    "hudsonreed", "isabellaflores", "jacobturner", "jaspercox", "josephperry",
    "julianbailey", "laylamitchell", "leoviola", "leviparker", "liamcarter",
    "lillianhughes", "loganrivera", "lucasmorgan", "lucybell", "madisoncook",
    "masonbailey", "matthewedwards", "miagriffin", "nataliepeterson", "nathanielwood",
    "noahbrooks", "norafernandez", "oliverbennett", "owenchavez", "peneloperyan",
    "rileystewart", "samueljenkins", "scarlettlong", "sebastianpowell", "sophiarussell",
    "theodorebell", "victoriakelly", "violetward", "williammorris", "zoephillips",
]


def _generate_mail_local_prefix():
    return random.choice(_FOREIGN_NAME_PREFIXES) + "".join(random.choices(string.ascii_lowercase, k=5))


def _clean_base_url(value):
    return (value or "").strip().rstrip("/")


def _get_moemail_url():
    return _clean_base_url(_MOEMAIL_URL or os.environ.get(_MOEMAIL_ENV_URL))


def _get_moemail_api_key():
    return (_MOEMAIL_API_KEY or os.environ.get(_MOEMAIL_ENV_API_KEY) or "").strip()


def _get_moemail_default_domain():
    return (_MOEMAIL_DEFAULT_DOMAIN or os.environ.get(_MOEMAIL_ENV_DEFAULT_DOMAIN) or "").strip()


def _is_moemail_configured():
    return bool(_get_moemail_url() and _get_moemail_api_key())


def configure_moemail(base_url=None, api_key=None, default_domain=None):
    global _MOEMAIL_URL, _MOEMAIL_API_KEY, _MOEMAIL_DEFAULT_DOMAIN
    _MOEMAIL_URL = _clean_base_url(base_url)
    _MOEMAIL_API_KEY = (api_key or "").strip()
    _MOEMAIL_DEFAULT_DOMAIN = (default_domain or "").strip()


def _get_tempmailio_domains():
    global _TEMPMĀILIO_DOMAINS_CACHE, _TEMPMĀILIO_DOMAINS_CACHE_TIME
    now = time.time()
    if _TEMPMĀILIO_DOMAINS_CACHE and (now - _TEMPMĀILIO_DOMAINS_CACHE_TIME) < 600:
        return _TEMPMĀILIO_DOMAINS_CACHE
    try:
        resp = make_request("GET", _TEMPMĀILIO_URL, "/api/v2/domains",
                            headers={"Accept": "application/json"},
                            timeout=30, use_proxy=True)
        data = _safe_data(resp)
        domains = data.get("domains", []) if isinstance(data, dict) else []
        _TEMPMĀILIO_DOMAINS_CACHE = domains
        _TEMPMĀILIO_DOMAINS_CACHE_TIME = now
        return domains
    except Exception:
        if _TEMPMĀILIO_DOMAINS_CACHE:
            return _TEMPMĀILIO_DOMAINS_CACHE
        return []


def _get_tempmailol_domains():
    global _TEMPMĀILLOL_DOMAINS_CACHE, _TEMPMĀILLOL_DOMAINS_CACHE_TIME
    now = time.time()
    if _TEMPMĀILLOL_DOMAINS_CACHE and (now - _TEMPMĀILLOL_DOMAINS_CACHE_TIME) < 600:
        return _TEMPMĀILLOL_DOMAINS_CACHE
    try:
        domains = []
        resp = make_request("GET", _TEMPMĀILLOL_URL, "/generate",
                            timeout=15, use_proxy=True)
        data = _safe_data(resp)
        addr = data.get("address", "") if isinstance(data, dict) else ""
        if "@" in addr:
            domain = addr.split("@")[1]
            domains.append(domain)
        _TEMPMĀILLOL_DOMAINS_CACHE = domains
        _TEMPMĀILLOL_DOMAINS_CACHE_TIME = now
        return domains
    except Exception:
        if _TEMPMĀILLOL_DOMAINS_CACHE:
            return _TEMPMĀILLOL_DOMAINS_CACHE
        return []


def _get_mailtm_domains():
    resp = make_request("GET", _MAILTM_URL, "/domains",
                        headers={"Accept": "application/json", "Cache-Control": "no-cache"},
                        timeout=15, use_proxy=True)
    data = _safe_data(resp)
    if isinstance(data, list):
        return [d["domain"] for d in data if isinstance(d, dict) and d.get("isActive")]
    return []


def get_available_domains():
    domains = {_GPTMAIL_POOL_LABEL}
    if _is_moemail_configured():
        domains.add(_MOEMAIL_POOL_LABEL)

    try:
        resp = make_request("GET", _MAILTM_URL, "/domains",
                            headers={"Accept": "application/json", "Cache-Control": "no-cache"},
                            timeout=15, use_proxy=True)
        data = _safe_data(resp)
        if isinstance(data, list):
            for d in data:
                if isinstance(d, dict) and d.get("isActive"):
                    domain = d["domain"]
                    if domain not in _BLOCKED_DOMAINS:
                        domains.add(domain)
    except Exception:
        pass

    try:
        tempmailio_domains = _get_tempmailio_domains()
        for d in tempmailio_domains:
            if d not in _BLOCKED_DOMAINS:
                domains.add(d)
    except Exception:
        pass

    try:
        tempmailol_domains = _get_tempmailol_domains()
        for d in tempmailol_domains:
            if d not in _BLOCKED_DOMAINS:
                domains.add(d)
    except Exception:
        pass

    if domains:
        return sorted(domains)
    return sorted([d for d in _FALLBACK_DOMAINS if d not in _BLOCKED_DOMAINS])


def _try_create_mailtm(local, password, domain):
    email = f"{local}@{domain}"
    resp = make_request("POST", _MAILTM_URL, "/accounts", headers={
        "Accept": "application/json",
        "Content-Type": "application/json",
    }, body={"address": email, "password": password}, timeout=15, use_proxy=True)
    data = _safe_data(resp)
    if isinstance(data, dict) and resp["status_code"] == 201 and data.get("id"):
        token_resp = make_request("POST", _MAILTM_URL, "/token", headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        }, body={"address": email, "password": password}, timeout=15, use_proxy=True)
        token_data = _safe_data(token_resp)
        token = token_data.get("token") if isinstance(token_data, dict) else None
        if not token:
            raise RuntimeError(f"获取token失败: {token_resp['data']}")
        return {"email": email, "token": token, "base_url": _MAILTM_URL, "type": "mailtm"}
    return None


def _try_create_tempmailio(local, domain):
    resp = make_request("POST", _TEMPMĀILIO_URL, "/api/v2/email/new",
                        headers={"Accept": "application/json", "Content-Type": "application/json"},
                        body={"local_part": local, "domain": domain},
                        timeout=30, use_proxy=True)
    data = _safe_data(resp)
    if not isinstance(data, dict):
        raise RuntimeError(f"Temp-Mail创建失败: {data}")
    email = data.get("email")
    token = data.get("token")
    if not email or not token:
        raise RuntimeError(f"Temp-Mail创建失败: {data}")
    return {"email": email, "token": email, "base_url": _TEMPMĀILIO_URL, "type": "tempmailio"}


def _try_create_tempmailol(local, domain):
    resp = make_request("GET", _TEMPMĀILLOL_URL, "/generate",
                        timeout=15, use_proxy=True)
    data = _safe_data(resp)
    if not isinstance(data, dict):
        raise RuntimeError(f"TempMail.lol创建失败: {data}")
    email = data.get("address")
    token = data.get("token")
    if not email or not token:
        raise RuntimeError(f"TempMail.lol创建失败: {data}")
    return {"email": email, "token": token, "base_url": _TEMPMĀILLOL_URL, "type": "tempmailol"}


def _moemail_request(method, path, payload=None):
    base_url = _get_moemail_url()
    api_key = _get_moemail_api_key()
    if not base_url or not api_key:
        raise RuntimeError("MoeHail API 未配置：请填写 moemail_base_url 和 moemail_api_key")
    resp = make_request(method, base_url, path,
                        headers={
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                            "X-API-Key": api_key,
                        },
                        body=payload, timeout=20, use_proxy=True)
    data = resp.get("data")
    if isinstance(data, dict):
        if data.get("error"):
            raise RuntimeError(f"MoeHail API error: {data['error']}")
        return data
    raise RuntimeError(f"MoeHail API invalid response: {data}")


def _get_moemail_domains():
    data = _moemail_request("GET", "/api/config")
    default_domain = _get_moemail_default_domain()
    raw = data.get("emailDomains", default_domain)
    domains = [item.strip() for item in str(raw).split(",") if item.strip()]
    return domains or ([default_domain] if default_domain else [])


def _try_create_moemail(domain=None):
    domains = _get_moemail_domains()
    if not domains:
        raise RuntimeError("MoeHail API 未返回可用邮箱域名，请检查默认域名或服务端 /api/config")
    if domain and domain not in domains:
        raise RuntimeError(f"MoeHail domain unavailable: {domain}")
    default_domain = _get_moemail_default_domain()
    selected_domain = domain or (default_domain if default_domain in domains else random.choice(domains))
    payload = {
        "name": _generate_mail_local_prefix(),
        "expiryTime": _MOEMAIL_EXPIRY_TIME,
        "domain": selected_domain,
    }
    data = _moemail_request("POST", "/api/emails/generate", payload)
    email_id = data.get("id")
    email = data.get("email") or data.get("address")
    if not email_id or not email:
        raise RuntimeError(f"MoeHail create mailbox failed: {data}")
    return {"email": email, "token": email_id, "base_url": _get_moemail_url(), "type": "moemail"}


def _collect_gptmail_domains(value, bucket):
    if isinstance(value, str):
        domain = value.strip().lower()
        if re.fullmatch(r"[a-z0-9.-]+\.[a-z]{2,}", domain) and domain not in _BLOCKED_DOMAINS:
            bucket.append(domain)
        return
    if isinstance(value, dict):
        for item in value.values():
            _collect_gptmail_domains(item, bucket)
        return
    if isinstance(value, list):
        for item in value:
            _collect_gptmail_domains(item, bucket)


def _collect_text_fragments(value, bucket):
    if value is None:
        return
    if isinstance(value, str):
        text = value.strip()
        if text:
            bucket.append(text)
        return
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        bucket.append(str(value))
        return
    if isinstance(value, dict):
        for item in value.values():
            _collect_text_fragments(item, bucket)
        return
    if isinstance(value, list):
        for item in value:
            _collect_text_fragments(item, bucket)


def _extract_first_token(value):
    if isinstance(value, dict):
        auth = value.get("auth")
        if isinstance(auth, dict):
            token = auth.get("token")
            if isinstance(token, str) and token.strip():
                return token.strip()
        token = value.get("token")
        if isinstance(token, str) and token.strip():
            return token.strip()
        for item in value.values():
            token = _extract_first_token(item)
            if token:
                return token
        return None
    if isinstance(value, list):
        for item in value:
            token = _extract_first_token(item)
            if token:
                return token
    return None


def _extract_gptmail_messages(value):
    if isinstance(value, list):
        if any(isinstance(item, dict) for item in value):
            return [item for item in value if isinstance(item, dict)]
        return []
    if isinstance(value, dict):
        for key in ("emails", "messages", "items", "results", "data"):
            nested = value.get(key)
            if isinstance(nested, list):
                return [item for item in nested if isinstance(item, dict)]
            if isinstance(nested, dict):
                found = _extract_gptmail_messages(nested)
                if found:
                    return found
    return []


def _get_gptmail_public_domains():
    resp = make_request("GET", _GPTMAIL_URL, "/api/domains/public",
                        headers={"Accept": "application/json"},
                        timeout=20, use_proxy=True)
    raw = resp.get("data")
    domains = []
    _collect_gptmail_domains(raw, domains)
    domains = sorted(set(domains))
    if not domains:
        raise RuntimeError("GPTMail create failed: no public domains returned")
    return domains


def _request_gptmail_inbox_token(email):
    resp = make_request("POST", _GPTMAIL_URL, "/api/inbox-token",
                        headers={
                            "Accept": "application/json",
                            "Content-Type": "application/json",
                        },
                        body={"email": email}, timeout=20, use_proxy=True)
    raw = resp.get("data")
    token = _extract_first_token(raw)
    if not token:
        raise RuntimeError(f"GPTMail token fetch failed: {raw}")
    return token


def _fetch_gptmail_payload(token, email=None):
    params = {"email": email} if email else None
    resp = make_request("GET", _GPTMAIL_URL, "/api/emails",
                        headers={"Accept": "application/json", "X-Inbox-Token": token},
                        params=params, timeout=20, use_proxy=True)
    data = _safe_data(resp)
    if isinstance(data, dict) and isinstance(data.get("data"), (dict, list)):
        return data.get("data")
    return data


def _extract_code_from_gptmail_payload(payload):
    fragments = []
    _collect_text_fragments(payload, fragments)
    if not fragments:
        return None
    return _find_code("\n".join(fragments))


def _try_create_gptmail():
    domains = _get_gptmail_public_domains()
    local = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    email = f"{local}@{random.choice(domains)}"
    inbox_token = _request_gptmail_inbox_token(email)
    return {"email": email, "token": inbox_token, "base_url": _GPTMAIL_URL, "type": "gptmail"}


def create_mail_account(force_domain=None):
    local = _generate_mail_local_prefix()
    password = "".join(random.choices(string.ascii_letters + string.digits, k=12))

    if force_domain:
        if isinstance(force_domain, str) and force_domain.startswith("GPTMail"):
            return _try_create_gptmail()
        if isinstance(force_domain, str) and force_domain.startswith("MoeHail"):
            return _try_create_moemail()
        try:
            moemail_domains = _get_moemail_domains()
            if force_domain in moemail_domains:
                return _try_create_moemail(force_domain)
        except Exception:
            pass
        try:
            mailtm_domains = _get_mailtm_domains()
            if force_domain in mailtm_domains:
                result = _try_create_mailtm(local, password, force_domain)
                if result:
                    return result
        except Exception:
            pass
        try:
            tempmailio_domains = _get_tempmailio_domains()
            if force_domain in tempmailio_domains:
                result = _try_create_tempmailio(local, force_domain)
                if result:
                    return result
        except Exception:
            pass
        raise RuntimeError(f"指定域名不可用: {force_domain}")

    candidates = [("gptmail", ["auto"])]
    if _is_moemail_configured():
        candidates.append(("moemail", ["auto"]))

    try:
        tempmailio_domains = [d for d in _get_tempmailio_domains() if d not in _BLOCKED_DOMAINS]
        if tempmailio_domains:
            candidates.append(("tempmailio", tempmailio_domains))
    except Exception:
        pass

    try:
        mailtm_domains = [d for d in _get_mailtm_domains() if d not in _BLOCKED_DOMAINS]
        if mailtm_domains:
            candidates.append(("mailtm", mailtm_domains))
    except Exception:
        pass

    try:
        tempmailol_domains = [d for d in _get_tempmailol_domains() if d not in _BLOCKED_DOMAINS]
        if tempmailol_domains:
            candidates.append(("tempmailol", tempmailol_domains))
    except Exception:
        pass

    for ptype, domains in candidates:
        try:
            domain = random.choice(domains)
            if ptype == "tempmailio":
                result = _try_create_tempmailio(local, domain)
            elif ptype == "mailtm":
                result = _try_create_mailtm(local, password, domain)
            elif ptype == "tempmailol":
                result = _try_create_tempmailol(local, domain)
            elif ptype == "gptmail":
                result = _try_create_gptmail()
            elif ptype == "moemail":
                result = _try_create_moemail()
            else:
                continue
            if result:
                return result
        except Exception:
            continue

    raise RuntimeError("所有邮箱服务商均不可用")


def _safe_data(resp):
    data = resp["data"]
    if isinstance(data, str):
        return {}
    if isinstance(data, (dict, list)):
        return data
    return {}


def _find_code(value):
    if not value:
        return None
    match = re.search(r"\b(\d{6})\b", str(value))
    return match.group(1) if match else None


def _fetch_code_mailtm(email, token, stop_check=None):
    last_error = None
    poll_count = 0

    while True:
        if stop_check and stop_check():
            raise RuntimeError('用户停止')

        poll_count += 1
        try:
            resp = make_request("GET", _MAILTM_URL, "/messages", headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {token}",
            }, timeout=15, use_proxy=True)

            messages = _safe_data(resp)
            if isinstance(messages, dict):
                messages = messages.get("hydra:member", [])
            if not isinstance(messages, list):
                messages = []

            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                subject = msg.get("subject", "")
                intro = msg.get("intro", "")
                summary_code = _find_code(f"{subject} {intro}")
                if summary_code:
                    return summary_code

                try:
                    msg_id = msg.get("id")
                    if not msg_id:
                        continue
                    detail = make_request(
                        "GET", _MAILTM_URL, f"/messages/{msg_id}",
                        headers={
                            "Accept": "application/json",
                            "Authorization": f"Bearer {token}",
                        }, timeout=15, use_proxy=True,
                    )
                    detail_data = _safe_data(detail)
                    body = detail_data.get("text", "") or detail_data.get("html", "")
                    body_code = _find_code(body)
                    if body_code:
                        return body_code
                except Exception as e:
                    last_error = e

            if poll_count > 30:
                raise RuntimeError(f"收取验证码超时: {email} 已轮询{poll_count}次未收到验证码")
            time.sleep(3)
        except Exception as e:
            last_error = e
            time.sleep(5)
            if poll_count > 30:
                raise RuntimeError(f"收取验证码超时: {email} {last_error}")


def _fetch_code_tempmailio(email, stop_check=None):
    last_error = None
    poll_count = 0
    seen_ids = set()

    while True:
        if stop_check and stop_check():
            raise RuntimeError('用户停止')

        poll_count += 1
        try:
            resp = make_request("GET", _TEMPMĀILIO_URL,
                                f"/api/v2/email/{email}/messages",
                                headers={"Accept": "application/json"},
                                timeout=30, use_proxy=True)
            messages = _safe_data(resp)

            if not isinstance(messages, list):
                continue

            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                msg_id = msg.get("id")
                if msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)

                subject = msg.get("subject", "")
                body = msg.get("body_text", "") or msg.get("body_html", "")
                snippet = msg.get("snippet", "")
                code = _find_code(f"{subject} {snippet} {body}")
                if code:
                    return code

                try:
                    detail = make_request("GET", _TEMPMĀILIO_URL,
                                          f"/api/v2/email/{email}/messages/{msg_id}",
                                          headers={"Accept": "application/json"},
                                          timeout=30, use_proxy=True)
                    detail_data = _safe_data(detail)
                    full_body = detail_data.get("body_text", "") or detail_data.get("body_html", "")
                    full_code = _find_code(full_body)
                    if full_code:
                        return full_code
                except Exception as e:
                    last_error = e

            if poll_count > 30:
                raise RuntimeError(f"收取验证码超时: {email} 已轮询{poll_count}次未收到验证码")
            time.sleep(3)
        except Exception as e:
            last_error = e
            time.sleep(5)
            if poll_count > 30:
                raise RuntimeError(f"收取验证码超时: {email} {last_error}")


def _fetch_code_tempmailol(email, token, stop_check=None):
    last_error = None
    poll_count = 0
    seen_ids = set()

    while True:
        if stop_check and stop_check():
            raise RuntimeError('用户停止')

        poll_count += 1
        try:
            resp = make_request("GET", _TEMPMĀILLOL_URL, f"/auth/{token}",
                                headers={"Accept": "application/json"},
                                timeout=15, use_proxy=True)
            data = _safe_data(resp)
            emails = data.get("email", []) if isinstance(data, dict) else []

            if not isinstance(emails, list):
                continue

            for msg in emails:
                if not isinstance(msg, dict):
                    continue
                msg_id = msg.get("unique_id") or msg.get("id")
                if msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)

                subject = msg.get("subject", "")
                body = msg.get("body", "") or msg.get("html", "")
                code = _find_code(f"{subject} {body}")
                if code:
                    return code

            if poll_count > 30:
                raise RuntimeError(f"收取验证码超时: {email} 已轮询{poll_count}次未收到验证码")
            time.sleep(3)
        except Exception as e:
            last_error = e
            time.sleep(5)
            if poll_count > 30:
                raise RuntimeError(f"收取验证码超时: {email} {last_error}")


def _fetch_code_moemail(email, token, stop_check=None):
    last_error = None
    seen_ids = set()

    for poll_count in range(1, _MOEMAIL_MAX_POLL_TIMES + 1):
        if stop_check and stop_check():
            raise RuntimeError("User stopped")

        try:
            message_data = _moemail_request("GET", f"/api/emails/{token}")
            messages = message_data.get("messages", []) if isinstance(message_data, dict) else []

            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                msg_id = msg.get("id")
                if not msg_id or msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)

                detail = _moemail_request("GET", f"/api/emails/{token}/{msg_id}")
                message = detail.get("message", {}) if isinstance(detail, dict) else {}
                subject = message.get("subject", "")
                content = message.get("content", "")
                html = message.get("html", "")
                code = _find_code(f"{subject}\n{content}\n{html}")
                if code:
                    return code

            if poll_count < _MOEMAIL_MAX_POLL_TIMES:
                time.sleep(_MOEMAIL_POLL_INTERVAL)
        except Exception as e:
            last_error = e
            if poll_count < _MOEMAIL_MAX_POLL_TIMES:
                time.sleep(_MOEMAIL_POLL_INTERVAL)

    raise RuntimeError(f"MoeHail???????: {email} {last_error or ''}".strip())


def _fetch_code_gptmail(email, token, stop_check=None):
    last_error = None
    poll_count = 0

    while True:
        if stop_check and stop_check():
            raise RuntimeError('User stopped')

        poll_count += 1
        try:
            payload = _fetch_gptmail_payload(token, email=email)
            messages = _extract_gptmail_messages(payload)
            if not messages:
                fallback_payload = _fetch_gptmail_payload(token)
                fallback_messages = _extract_gptmail_messages(fallback_payload)
                if fallback_messages:
                    payload = fallback_payload
                    messages = fallback_messages

            code = _extract_code_from_gptmail_payload(messages or payload)
            if code:
                return code

            if poll_count > 30:
                raise RuntimeError(f"Verification code timeout: {email} polled {poll_count} times with no code")
            time.sleep(3)
        except Exception as e:
            last_error = e
            time.sleep(5)
            if poll_count > 30:
                raise RuntimeError(f"Verification code timeout: {email} {last_error}")


def fetch_verification_code(email, token, base_url=None, stop_check=None, provider_type=None):
    if provider_type == "gptmail":
        return _fetch_code_gptmail(email, token, stop_check=stop_check)

    if provider_type == "moemail":
        return _fetch_code_moemail(email, token, stop_check=stop_check)

    if provider_type == "tempmailio":
        return _fetch_code_tempmailio(email, stop_check=stop_check)

    if provider_type == "tempmailol":
        return _fetch_code_tempmailol(email, token, stop_check=stop_check)

    return _fetch_code_mailtm(email, token, stop_check=stop_check)


def configure_mail(force_domain=None):
    global _FORCE_DOMAIN
    _FORCE_DOMAIN = force_domain
