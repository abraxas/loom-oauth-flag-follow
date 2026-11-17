"""Lab harness for the v1.9.0 OAuth flag-gated clear leftover.

Product routers stay unmodified. Product `_get_oauth2_token` and
`_build_headers` still run.

- Bearer lab-demo is t-admin + g-admins-demo. No unauthenticated bypass.
- Secrets Manager is a file. get_secret raises when the name is absent so
  resolve_oauth2_client_secret falls through to the plaintext column.
- One unmigrated MCP row is seeded with has_oauth2_secret unset.
- safe_get / safe_post / is_trusted_oauth_host are stubbed only for the lab IdP.
"""

from __future__ import annotations

import json
import logging
import threading
import urllib.parse
from pathlib import Path
from typing import Any

logger = logging.getLogger("lab_patch")

SM_PATH = Path("/tmp/loom-190-oauth-flag-sm.json")
SERVER_NAME = "lab-oauth"
PRE_SECRET = "lab-pre-oauth-secret"
CTRL_SECRET = "lab-ctrl-oauth-secret"
WITNESS = "LOOM-190-OAUTH-FLAG-FOLLOW-WITNESS"
CTRL_TOKEN = "LOOM-190-OAUTH-FLAG-FOLLOW-CONTROL"
IDP_HOST = "idp.lab.invalid"
WELL_KNOWN = f"https://{IDP_HOST}/.well-known/openid-configuration"
TOKEN_URL = f"https://{IDP_HOST}/oauth/token"
OLD_ENDPOINT = "http://10.255.255.1/old"

_SM_LOCK = threading.Lock()
_HOOKED = False
_AUTH = False
_SECRETS = False
_NET = False
_DB = False


def _read_sm() -> dict[str, str]:
    if not SM_PATH.exists():
        return {}
    raw = SM_PATH.read_text(encoding="utf-8")
    if not raw.strip():
        return {}
    loaded = json.loads(raw)
    if not isinstance(loaded, dict):
        return {}
    return {str(key): str(value) for key, value in loaded.items()}


def _write_sm(data: dict[str, str]) -> None:
    tmp = SM_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    tmp.replace(SM_PATH)


def _json_response(method: str, url: str, payload: dict[str, object], status: int = 200) -> Any:
    # raise_for_status() refuses a response that has no request attached.
    import httpx

    return httpx.Response(status, json=payload, request=httpx.Request(method, url))


def _patch_auth(mod: Any) -> None:
    global _AUTH
    if getattr(mod, "_lab_oauth_auth", False) or _AUTH:
        return
    import functools
    import inspect

    orig = mod.get_current_user
    user_info = mod.UserInfo
    derive_scopes = mod.derive_scopes
    tokens = {
        "lab-demo": ("demo-admin", "lab-demo", ["t-admin", "g-admins-demo"]),
    }

    @functools.wraps(orig)
    def get_current_user(request: Any) -> Any:
        auth_header = request.headers.get("Authorization", "")
        token = auth_header[7:] if auth_header.startswith("Bearer ") else ""
        if token in tokens:
            username, sub, groups = tokens[token]
            return user_info(
                sub=sub,
                username=username,
                groups=groups,
                scopes=derive_scopes(groups),
                idp_type="lab",
            )
        return orig(request)

    get_current_user.__signature__ = inspect.signature(orig)
    get_current_user.__annotations__ = dict(getattr(orig, "__annotations__", {}))
    mod.get_current_user = get_current_user
    mod._lab_oauth_auth = True
    _AUTH = True
    logger.info("lab harness: get_current_user wrapped")


def _patch_secrets(mod: Any) -> None:
    global _SECRETS
    if getattr(mod, "_lab_oauth_secrets", False) or _SECRETS:
        return

    def store_secret(name: str, secret_value: str, region: str, description: str = "") -> str:
        del region, description
        with _SM_LOCK:
            data = _read_sm()
            data[name] = secret_value
            _write_sm(data)
        logger.info("lab harness: store_secret")
        return f"arn:lab:{name}"

    def get_secret(name: str, region: str) -> str:
        # A miss must raise. resolve_oauth2_client_secret treats any exception
        # as "not in Secrets Manager" and returns the legacy column.
        del region
        with _SM_LOCK:
            data = _read_sm()
        if name not in data:
            raise KeyError(name)
        return data[name]

    def delete_secret(name: str, region: str) -> None:
        del region
        with _SM_LOCK:
            data = _read_sm()
            data.pop(name, None)
            _write_sm(data)
        logger.info("lab harness: delete_secret")

    mod.store_secret = store_secret
    mod.get_secret = get_secret
    mod.delete_secret = delete_secret
    mod._lab_oauth_secrets = True
    _SECRETS = True
    logger.info("lab harness: Secrets Manager file %s", SM_PATH.name)


def _patch_net(mod: Any) -> None:
    global _NET
    if getattr(mod, "_lab_oauth_net", False) or _NET:
        return
    orig_get = mod.safe_get
    orig_post = mod.safe_post
    orig_trusted = mod.is_trusted_oauth_host

    def safe_get(url: str, *, headers: dict[str, str] | None = None, timeout: float = 10) -> Any:
        if url == WELL_KNOWN:
            return _json_response("GET", url, {"token_endpoint": TOKEN_URL})
        return orig_get(url, headers=headers, timeout=timeout)

    def safe_post(
        url: str,
        *,
        data: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float = 10,
    ) -> Any:
        if url == TOKEN_URL:
            secret = (data or {}).get("client_secret", "")
            if secret == PRE_SECRET:
                logger.info("lab harness: token mint witness")
                return _json_response("POST", url, {"access_token": WITNESS})
            if secret == CTRL_SECRET:
                logger.info("lab harness: token mint control")
                return _json_response("POST", url, {"access_token": CTRL_TOKEN})
            return _json_response("POST", url, {"error": "invalid_client"}, status=401)
        return orig_post(url, data=data, headers=headers, timeout=timeout)

    def is_trusted_oauth_host(url: str, trusted_hosts: set[str]) -> bool:
        host = urllib.parse.urlparse(url).hostname or ""
        if host.lower() == IDP_HOST:
            return True
        return bool(orig_trusted(url, trusted_hosts))

    mod.safe_get = safe_get
    mod.safe_post = safe_post
    mod.is_trusted_oauth_host = is_trusted_oauth_host
    mod._lab_oauth_net = True
    _NET = True
    logger.info("lab harness: lab IdP stubs installed")


def _rebind_oauth_client(mod: Any) -> None:
    """Point the service module at the stubbed net_guard names.

    mcp.py and a2a.py bind safe_get / safe_post / is_trusted_oauth_host with
    import-from. `_get_oauth2_token` looks those names up on its own module.
    """
    import sys

    net = sys.modules.get("app.services.net_guard")
    if net is None or not getattr(net, "_lab_oauth_net", False):
        return
    if not hasattr(mod, "safe_get"):
        return
    mod.safe_get = net.safe_get
    mod.safe_post = net.safe_post
    mod.is_trusted_oauth_host = net.is_trusted_oauth_host


def _seed_unmigrated() -> None:
    from datetime import datetime

    from app.db import SessionLocal
    from app.models.mcp import McpServer

    db = SessionLocal()
    try:
        existing = db.query(McpServer).filter(McpServer.name == SERVER_NAME).first()
        if existing:
            logger.info("lab harness: unmigrated MCP row already seeded id=%s", existing.id)
            return
        now = datetime.utcnow()
        server = McpServer(
            name=SERVER_NAME,
            description="unmigrated-oauth",
            endpoint_url=OLD_ENDPOINT,
            transport_type="streamable_http",
            status="active",
            auth_type="oauth2",
            oauth2_well_known_url=WELL_KNOWN,
            oauth2_client_id="lab-client",
            oauth2_client_secret=PRE_SECRET,
            has_oauth2_secret=None,
            delegation_mode="m2m",
            created_at=now,
            updated_at=now,
        )
        server.set_tags({"loom:group": "demo"})
        db.add(server)
        db.commit()
        logger.info("lab harness: seeded unmigrated MCP row id=%s", server.id)
    except Exception:
        db.rollback()
        logger.exception("lab harness: unmigrated seed failed")
        raise
    finally:
        db.close()


def _patch_db(mod: Any) -> None:
    global _DB
    if getattr(mod, "_lab_oauth_db", False) or _DB:
        return
    orig = mod.init_db

    def init_db() -> None:
        orig()
        _seed_unmigrated()

    mod.init_db = init_db
    mod._lab_oauth_db = True
    _DB = True
    logger.info("lab harness: init_db wrapped")


def install() -> None:
    import sys

    auth = sys.modules.get("app.dependencies.auth")
    if auth is not None:
        _patch_auth(auth)
    secrets = sys.modules.get("app.services.secrets")
    if secrets is not None:
        _patch_secrets(secrets)
    net = sys.modules.get("app.services.net_guard")
    if net is not None:
        _patch_net(net)
    for name in ("app.services.mcp", "app.services.a2a"):
        client = sys.modules.get(name)
        if client is not None:
            _rebind_oauth_client(client)
    db = sys.modules.get("app.db")
    if db is not None:
        _patch_db(db)


def install_import_hook() -> None:
    global _HOOKED
    if _HOOKED:
        return
    import builtins

    orig_import = builtins.__import__
    watched = {
        "app.dependencies.auth": _patch_auth,
        "app.services.secrets": _patch_secrets,
        "app.services.net_guard": _patch_net,
        "app.db": _patch_db,
    }
    rebound = {"app.services.mcp", "app.services.a2a"}

    def hooked(name, globals=None, locals=None, fromlist=(), level=0):
        mod = orig_import(name, globals, locals, fromlist, level)
        mod_name = getattr(mod, "__name__", "") or ""
        patch = watched.get(name) or watched.get(mod_name)
        if patch is not None:
            patch(mod)
        if name in rebound or mod_name in rebound:
            _rebind_oauth_client(mod)
        return mod

    builtins.__import__ = hooked
    _HOOKED = True
