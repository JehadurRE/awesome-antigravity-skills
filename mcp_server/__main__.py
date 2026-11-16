"""CLI and MCP stdio entrypoint for canva-skills-mcp."""

from __future__ import annotations

import argparse
import json

from .auth import AccountManager, start_oauth_flow
from .server import discover_skills, run_stdio_server


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified Canva Skills MCP Server & OAuth CLI")
    parser.add_argument("--connect", metavar="ACCOUNT_ID", help="Connect a Canva account via OAuth 2.0 PKCE")
    parser.add_argument("--name", help="Display name when using --connect")
    parser.add_argument("--port", type=int, default=8080, help="Local OAuth callback port (default: 8080)")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open browser during --connect")
    parser.add_argument("--accounts", action="store_true", help="List connected Canva accounts as JSON")
    parser.add_argument("--switch", metavar="ACCOUNT_ID", nargs="?", const="", help="Switch or rotate active account")
    parser.add_argument("--list-skills", action="store_true", help="List bundled Antigravity skills")
    args = parser.parse_args()

    mgr = AccountManager()

    if args.connect:
        res = start_oauth_flow(
            account_id=args.connect,
            name=args.name,
            port=args.port,
            open_browser=not args.no_browser,
            wait_for_callback=True,
            manager=mgr,
        )
        print(json.dumps(res, indent=2))
        return

    if args.accounts:
        print(json.dumps(mgr.list_accounts(), indent=2))
        return

    if args.switch is not None:
        target = args.switch or None
        aid, acc = mgr.switch_account(target)
        print(json.dumps({"active_account_id": aid, "name": (acc or {}).get("name")}, indent=2))
        return

    if args.list_skills:
        print(json.dumps(discover_skills(), indent=2))
        return

    run_stdio_server()


if __name__ == "__main__":
    main()
