"""Remote Canva MCP proxy with automatic 401 token refresh and quota_cooldown rotation."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from .auth import USER_AGENT, AccountManager

CANVA_MCP_URL = "https://mcp.canva.com/mcp"


def parse_mcp_http_response(raw_body: str, content_type: str = "") -> dict[str, Any]:
    """Parse either plain JSON or Server-Sent Events (SSE) JSON-RPC payloads from Canva MCP."""
    text = raw_body.strip()
    if not text:
        return {}

    if "text/event-stream" in content_type.lower() or text.startswith("event:") or text.startswith("data:"):
        last_json: dict[str, Any] | None = None
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("data:"):
                payload = stripped[5:].strip()
                if not payload or payload == "[DONE]":
                    continue
                try:
                    last_json = json.loads(payload)
                except json.JSONDecodeError:
                    continue
        if last_json is not None:
            return last_json

    return json.loads(text)


def _extract_quota_cooldown(response_obj: dict[str, Any]) -> tuple[bool, int | None]:
    """Detect Canva aiCreditQuotaError / quota_cooldown in MCP responses."""
    raw_str = json.dumps(response_obj)
    if "quota_cooldown" not in raw_str:
        return False, None

    cooldown_ends_at: int | None = None
    result = response_obj.get("result", {})
    meta = result.get("_meta", {}) if isinstance(result, dict) else {}
    quota_err = meta.get("com.canva/aiCreditQuotaError", {}) if isinstance(meta, dict) else {}
    usage = quota_err.get("quota_usage", {}) if isinstance(quota_err, dict) else {}
    if isinstance(usage, dict) and usage.get("cooldown_ends_at"):
        try:
            cooldown_ends_at = int(usage["cooldown_ends_at"])
        except (TypeError, ValueError):
            cooldown_ends_at = None

    return True, cooldown_ends_at


class CanvaRemoteClient:
    """Invokes https://mcp.canva.com/mcp with automatic token refresh and account rotation."""

    def __init__(self, manager: AccountManager | None = None, endpoint: str = CANVA_MCP_URL) -> None:
        self.manager = manager or AccountManager()
        self.endpoint = endpoint

    def _raw_rpc(self, method: str, params: dict[str, Any], access_token: str) -> dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": int(time.time() * 1000),
            "method": method,
            "params": params,
        }
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "User-Agent": USER_AGENT,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            ctype = resp.headers.get("Content-Type", "")
            raw = resp.read().decode("utf-8")
            return parse_mcp_http_response(raw, ctype)

    def request(
        self,
        method: str,
        params: dict[str, Any] | None = None,
        account_id: str | None = None,
        auto_rotate: bool = True,
    ) -> dict[str, Any]:
        """Send an authenticated JSON-RPC call to Canva MCP with retry on 401 and quota cooldown."""
        cfg = self.manager.load_config()
        accounts = cfg.get("accounts", {})
        if not accounts:
            raise RuntimeError(
                "No Canva accounts connected. Run `canva_connect_account` first to authenticate."
            )

        max_attempts = max(1, len(accounts)) if auto_rotate else 1
        tried_accounts: list[str] = []
        current_target = account_id

        for _ in range(max_attempts):
            aid, acc = self.manager.get_account(current_target)
            if not aid or not acc:
                break
            tried_accounts.append(aid)
            token = acc.get("access_token", "")

            if not token and acc.get("refresh_token"):
                self.manager.refresh_account_token(aid)
                _, acc = self.manager.get_account(aid)
                token = (acc or {}).get("access_token", "")

            try:
                resp = self._raw_rpc(method, params or {}, token)
            except urllib.error.HTTPError as exc:
                if exc.code == 401 and acc.get("refresh_token"):
                    self.manager.refresh_account_token(aid)
                    _, refreshed_acc = self.manager.get_account(aid)
                    resp = self._raw_rpc(method, params or {}, (refreshed_acc or {}).get("access_token", ""))
                else:
                    detail = exc.read().decode("utf-8", errors="replace")
                    raise RuntimeError(f"Canva MCP HTTP {exc.code}: {detail}") from exc

            hit_cooldown, ends_at = _extract_quota_cooldown(resp)
            if hit_cooldown and auto_rotate and len(accounts) > 1:
                self.manager.mark_cooldown(aid, ends_at=ends_at)
                next_id, _ = self.manager.switch_account()
                if next_id and next_id not in tried_accounts:
                    current_target = next_id
                    continue

            return {"account_id": aid, "response": resp}

        raise RuntimeError(
            f"All connected Canva accounts ({', '.join(tried_accounts)}) hit quota cooldown or failed."
        )

    def list_tools(self, account_id: str | None = None) -> dict[str, Any]:
        return self.request("tools/list", {}, account_id=account_id, auto_rotate=False)

    def call_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any] | None = None,
        account_id: str | None = None,
        auto_rotate: bool = True,
    ) -> dict[str, Any]:
        return self.request(
            "tools/call",
            {"name": tool_name, "arguments": arguments or {}},
            account_id=account_id,
            auto_rotate=auto_rotate,
        )
