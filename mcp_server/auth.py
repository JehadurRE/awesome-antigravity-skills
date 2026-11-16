"""Portable multi-account OAuth 2.0 PKCE & token manager for Canva MCP."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

CANVA_AUTHORIZE_URL = "https://mcp.canva.com/authorize"
CANVA_TOKEN_URL = "https://mcp.canva.com/token"
CANVA_REGISTER_URL = "https://mcp.canva.com/register"
DEFAULT_SCOPES = (
    "profile:read design:meta:read design:content:write design:content:read "
    "asset:read asset:write folder:read brandkit:read"
)
USER_AGENT = "Canva-Skills-MCP/1.0"


def get_state_dir() -> Path:
    """Resolve the portable state directory for tokens and account configs."""
    env_dir = os.environ.get("CANVA_STATE_DIR", "").strip()
    if env_dir:
        path = Path(os.path.expanduser(env_dir)).resolve()
    else:
        default_dir = Path.home() / ".canva-skills-mcp"
        legacy_dir = Path.home() / ".gemini"
        # Use ~/.canva-skills-mcp unless only a legacy ~/.gemini/canva_accounts.json exists
        if not (default_dir / "canva_accounts.json").exists() and (legacy_dir / "canva_accounts.json").exists():
            path = legacy_dir
        else:
            path = default_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def register_dynamic_client(redirect_uris: list[str], state_dir: Path | None = None) -> dict[str, Any]:
    """Register an OAuth 2.0 client dynamically with Canva MCP (RFC 7591)."""
    payload = {
        "client_name": "Awesome Antigravity Canva Skills MCP",
        "redirect_uris": redirect_uris,
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "client_secret_basic",
        "scope": DEFAULT_SCOPES,
    }
    req = urllib.request.Request(
        CANVA_REGISTER_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        client_info = json.loads(resp.read().decode("utf-8"))

    if state_dir is not None:
        _write_json(state_dir / "canva_client.json", client_info)
    return client_info


def resolve_client_credentials(
    redirect_uri: str,
    state_dir: Path | None = None,
    allow_dynamic_register: bool = True,
) -> tuple[str, str]:
    """Resolve OAuth client credentials from env, cached file, or RFC 7591 registration."""
    env_id = os.environ.get("CANVA_CLIENT_ID", "").strip()
    env_secret = os.environ.get("CANVA_CLIENT_SECRET", "").strip()
    if env_id:
        return env_id, env_secret

    base_dir = state_dir or get_state_dir()
    cached = _read_json(base_dir / "canva_client.json")
    if cached and cached.get("client_id"):
        return str(cached["client_id"]), str(cached.get("client_secret", ""))

    # Check existing accounts file for stored client credentials
    accounts_cfg = _read_json(base_dir / "canva_accounts.json") or {}
    for acc in accounts_cfg.get("accounts", {}).values():
        if acc.get("client_id"):
            return str(acc["client_id"]), str(acc.get("client_secret", ""))

    if not allow_dynamic_register:
        raise RuntimeError(
            "No Canva OAuth client credentials configured. Set CANVA_CLIENT_ID / CANVA_CLIENT_SECRET "
            "or enable dynamic registration against https://mcp.canva.com/register."
        )

    port = urllib.parse.urlparse(redirect_uri).port or 8080
    reg = register_dynamic_client(
        redirect_uris=[
            f"http://localhost:{port}/callback",
            f"http://127.0.0.1:{port}/callback",
        ],
        state_dir=base_dir,
    )
    return str(reg["client_id"]), str(reg.get("client_secret", ""))


def _exchange_or_refresh_token(
    form_data: dict[str, str],
    client_id: str,
    client_secret: str,
) -> dict[str, Any]:
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
    }
    body_dict = dict(form_data)
    if client_secret:
        auth_header = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
        headers["Authorization"] = f"Basic {auth_header}"
    else:
        body_dict["client_id"] = client_id

    req = urllib.request.Request(
        CANVA_TOKEN_URL,
        data=urllib.parse.urlencode(body_dict).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        tokens = json.loads(resp.read().decode("utf-8"))
    tokens["client_id"] = client_id
    if client_secret:
        tokens["client_secret"] = client_secret
    tokens["obtained_at"] = int(time.time())
    return tokens


class AccountManager:
    """Manages multiple Canva MCP accounts, token refresh, and cooldown rotation."""

    def __init__(self, state_dir: Path | None = None) -> None:
        self.state_dir = state_dir or get_state_dir()
        self.accounts_file = self.state_dir / "canva_accounts.json"
        self.primary_token_file = self.state_dir / "canva_token.json"

    def load_config(self) -> dict[str, Any]:
        cfg = _read_json(self.accounts_file)
        if cfg and isinstance(cfg.get("accounts"), dict):
            return cfg

        cfg = {"active_account_id": "account_1", "accounts": {}}
        primary = _read_json(self.primary_token_file)
        if primary and (primary.get("access_token") or primary.get("refresh_token")):
            cfg["accounts"]["account_1"] = {
                "name": "Primary Account",
                "token_file": str(self.primary_token_file),
                "client_id": primary.get("client_id", ""),
                "client_secret": primary.get("client_secret", ""),
                "refresh_token": primary.get("refresh_token", ""),
                "access_token": primary.get("access_token", ""),
                "last_cooldown_ends_at": 0,
            }
            self.save_config(cfg)
        return cfg

    def save_config(self, cfg: dict[str, Any]) -> None:
        _write_json(self.accounts_file, cfg)

    def list_accounts(self) -> dict[str, Any]:
        cfg = self.load_config()
        active_id = cfg.get("active_account_id")
        now = int(time.time())
        summary = []
        for aid, acc in cfg.get("accounts", {}).items():
            cooldown_end = int(acc.get("last_cooldown_ends_at") or 0)
            summary.append(
                {
                    "account_id": aid,
                    "name": acc.get("name", aid),
                    "active": aid == active_id,
                    "has_access_token": bool(acc.get("access_token")),
                    "has_refresh_token": bool(acc.get("refresh_token")),
                    "in_cooldown": cooldown_end > now,
                    "cooldown_remaining_seconds": max(0, cooldown_end - now),
                    "token_file": acc.get("token_file", ""),
                }
            )
        return {
            "state_dir": str(self.state_dir),
            "active_account_id": active_id,
            "total_accounts": len(summary),
            "accounts": summary,
        }

    def register_account(
        self,
        account_id: str,
        name: str,
        tokens: dict[str, Any],
        make_active: bool = True,
    ) -> dict[str, Any]:
        cfg = self.load_config()
        token_file = (
            self.primary_token_file
            if account_id == "account_1"
            else self.state_dir / f"canva_token_{account_id}.json"
        )
        _write_json(token_file, tokens)

        cfg.setdefault("accounts", {})[account_id] = {
            "name": name,
            "token_file": str(token_file),
            "client_id": tokens.get("client_id", ""),
            "client_secret": tokens.get("client_secret", ""),
            "refresh_token": tokens.get("refresh_token", ""),
            "access_token": tokens.get("access_token", ""),
            "last_cooldown_ends_at": 0,
        }
        if make_active or not cfg.get("active_account_id"):
            cfg["active_account_id"] = account_id
            _write_json(self.primary_token_file, tokens)

        self.save_config(cfg)
        return {"account_id": account_id, "name": name, "active": cfg["active_account_id"] == account_id}

    def get_account(self, account_id: str | None = None) -> tuple[str | None, dict[str, Any] | None]:
        cfg = self.load_config()
        accounts = cfg.get("accounts", {})
        if not accounts:
            return None, None

        aid = account_id or cfg.get("active_account_id")
        if aid not in accounts:
            aid = next(iter(accounts))
        acc = dict(accounts[aid])

        token_path = Path(acc["token_file"]) if acc.get("token_file") else None
        if token_path and token_path.exists():
            tdata = _read_json(token_path) or {}
            acc["access_token"] = tdata.get("access_token") or acc.get("access_token", "")
            acc["refresh_token"] = tdata.get("refresh_token") or acc.get("refresh_token", "")
            acc["client_id"] = tdata.get("client_id") or acc.get("client_id", "")
            acc["client_secret"] = tdata.get("client_secret") or acc.get("client_secret", "")
        return aid, acc

    def switch_account(self, target_id: str | None = None) -> tuple[str | None, dict[str, Any] | None]:
        cfg = self.load_config()
        accounts = cfg.get("accounts", {})
        if not accounts:
            return None, None

        current = cfg.get("active_account_id")
        acc_ids = list(accounts.keys())
        if target_id:
            if target_id not in accounts:
                raise KeyError(f"Unknown account_id '{target_id}'. Available: {acc_ids}")
            next_id = target_id
        else:
            if len(acc_ids) == 1:
                next_id = acc_ids[0]
            else:
                now = int(time.time())
                idx = acc_ids.index(current) if current in acc_ids else -1
                ordered = [acc_ids[(idx + 1 + offset) % len(acc_ids)] for offset in range(len(acc_ids))]
                # Prefer an account with credentials that is not currently in cooldown
                next_id = next(
                    (
                        aid
                        for aid in ordered
                        if aid != current
                        and (accounts[aid].get("access_token") or accounts[aid].get("refresh_token"))
                        and int(accounts[aid].get("last_cooldown_ends_at") or 0) <= now
                    ),
                    ordered[0],
                )

        cfg["active_account_id"] = next_id
        self.save_config(cfg)
        _, acc = self.get_account(next_id)
        if acc and acc.get("token_file") and Path(acc["token_file"]).exists():
            tdata = _read_json(Path(acc["token_file"]))
            if tdata:
                _write_json(self.primary_token_file, tdata)
        return next_id, acc

    def mark_cooldown(self, account_id: str, ends_at: int | None = None, duration_seconds: int = 300) -> int:
        cfg = self.load_config()
        acc = cfg.get("accounts", {}).get(account_id)
        if not acc:
            return 0
        target_ts = int(ends_at) if ends_at else int(time.time()) + duration_seconds
        acc["last_cooldown_ends_at"] = target_ts
        self.save_config(cfg)
        return target_ts

    def refresh_account_token(self, account_id: str | None = None) -> dict[str, Any]:
        aid, acc = self.get_account(account_id)
        if not aid or not acc:
            raise RuntimeError("No Canva accounts are registered yet. Run canva_connect_account first.")
        refresh_token = acc.get("refresh_token", "")
        if not refresh_token:
            raise RuntimeError(f"Account '{aid}' has no refresh_token stored.")

        client_id = acc.get("client_id") or os.environ.get("CANVA_CLIENT_ID", "")
        client_secret = acc.get("client_secret") or os.environ.get("CANVA_CLIENT_SECRET", "")
        if not client_id:
            client_id, client_secret = resolve_client_credentials(
                "http://localhost:8080/callback", state_dir=self.state_dir, allow_dynamic_register=False
            )

        new_tokens = _exchange_or_refresh_token(
            {"grant_type": "refresh_token", "refresh_token": refresh_token},
            client_id=client_id,
            client_secret=client_secret,
        )
        if "refresh_token" not in new_tokens:
            new_tokens["refresh_token"] = refresh_token

        cfg = self.load_config()
        stored = cfg["accounts"][aid]
        stored["access_token"] = new_tokens["access_token"]
        stored["refresh_token"] = new_tokens["refresh_token"]
        stored["client_id"] = client_id
        if client_secret:
            stored["client_secret"] = client_secret
        self.save_config(cfg)

        token_file = Path(stored["token_file"]) if stored.get("token_file") else self.primary_token_file
        _write_json(token_file, new_tokens)
        if cfg.get("active_account_id") == aid:
            _write_json(self.primary_token_file, new_tokens)

        return {
            "account_id": aid,
            "refreshed": True,
            "expires_in": new_tokens.get("expires_in"),
            "token_file": str(token_file),
        }


def _make_pkce_pair() -> tuple[str, str, str]:
    verifier = base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8").rstrip("=")
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("utf-8")).digest())
        .decode("utf-8")
        .rstrip("=")
    )
    state = base64.urlsafe_b64encode(os.urandom(16)).decode("utf-8").rstrip("=")
    return verifier, challenge, state


def start_oauth_flow(
    account_id: str = "account_1",
    name: str | None = None,
    port: int | None = None,
    open_browser: bool = True,
    wait_for_callback: bool = False,
    timeout_seconds: int = 600,
    manager: AccountManager | None = None,
) -> dict[str, Any]:
    """Start OAuth 2.0 PKCE flow on localhost callback and register tokens on completion."""
    mgr = manager or AccountManager()
    callback_port = port or int(os.environ.get("CANVA_OAUTH_PORT", "8080"))
    redirect_uri = f"http://localhost:{callback_port}/callback"
    display_name = name or account_id.replace("_", " ").title()

    client_id, client_secret = resolve_client_credentials(redirect_uri, state_dir=mgr.state_dir)
    verifier, challenge, state = _make_pkce_pair()

    auth_params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": DEFAULT_SCOPES,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "state": state,
    }
    auth_url = f"{CANVA_AUTHORIZE_URL}?{urllib.parse.urlencode(auth_params)}"
    result_box: dict[str, Any] = {"status": "pending"}
    done_event = threading.Event()

    class OAuthCallbackHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            return

        def do_GET(self) -> None:  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return

            query = urllib.parse.parse_qs(parsed.query)
            if "error" in query:
                err = query.get("error_description", query["error"])[0]
                result_box["status"] = "error"
                result_box["error"] = err
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"<h2>Canva OAuth Error</h2><p>{err}</p>".encode("utf-8"))
                done_event.set()
                return

            if "code" not in query:
                self.send_response(400)
                self.end_headers()
                return

            if query.get("state", [None])[0] != state:
                result_box["status"] = "error"
                result_box["error"] = "OAuth state mismatch"
                self.send_response(400)
                self.end_headers()
                done_event.set()
                return

            try:
                tokens = _exchange_or_refresh_token(
                    {
                        "grant_type": "authorization_code",
                        "code": query["code"][0],
                        "redirect_uri": redirect_uri,
                        "code_verifier": verifier,
                    },
                    client_id=client_id,
                    client_secret=client_secret,
                )
                reg_info = mgr.register_account(account_id, display_name, tokens, make_active=True)
                result_box["status"] = "connected"
                result_box["account"] = reg_info
                html = (
                    f"<!doctype html><html><body style='font-family:sans-serif;background:#0f172a;color:#f8fafc;"
                    f"display:flex;align-items:center;justify-content:center;height:100vh;margin:0'>"
                    f"<div style='background:#1e293b;padding:40px;border-radius:16px;text-align:center'>"
                    f"<h1 style='color:#38bdf8'>Canva Connected</h1>"
                    f"<p>Account <strong>{display_name}</strong> (<code>{account_id}</code>) is now active.</p>"
                    f"<p style='color:#94a3b8'>You may close this tab and return to your agent.</p>"
                    f"</div></body></html>"
                )
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            except Exception as exc:
                result_box["status"] = "error"
                result_box["error"] = str(exc)
                self.send_response(500)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"<h2>Token Exchange Failed</h2><pre>{exc}</pre>".encode("utf-8"))
            finally:
                done_event.set()

    server = HTTPServer(("127.0.0.1", callback_port), OAuthCallbackHandler)
    server.timeout = timeout_seconds

    def _serve_until_done() -> None:
        deadline = time.time() + timeout_seconds
        try:
            while not done_event.is_set() and time.time() < deadline:
                server.handle_request()
        finally:
            server.server_close()

    thread = threading.Thread(target=_serve_until_done, daemon=True)
    thread.start()

    if open_browser:
        try:
            webbrowser.open(auth_url)
        except Exception:
            pass

    if wait_for_callback:
        done_event.wait(timeout=timeout_seconds)
        return {"authorization_url": auth_url, "redirect_uri": redirect_uri, **result_box}

    return {
        "status": "listening",
        "account_id": account_id,
        "name": display_name,
        "redirect_uri": redirect_uri,
        "authorization_url": auth_url,
        "message": (
            "Open the authorization_url in a browser (use Incognito/another profile for a secondary account) "
            "and click Allow. The local callback server will automatically save and activate the tokens."
        ),
    }
