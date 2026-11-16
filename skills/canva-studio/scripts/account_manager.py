"""Portable CLI for managing multiple Canva MCP OAuth accounts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mcp_server.auth import AccountManager  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Canva MCP Multi-Account Manager")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list", help="List registered Canva accounts")

    sw = sub.add_parser("switch", help="Switch active Canva account (or rotate if omitted)")
    sw.add_argument("--account", default=None, help="Target account_id (e.g. account_2)")

    rf = sub.add_parser("refresh", help="Refresh OAuth token for an account")
    rf.add_argument("--account", default=None, help="Target account_id (defaults to active)")

    args = parser.parse_args()
    mgr = AccountManager()

    if args.command == "list":
        print(json.dumps(mgr.list_accounts(), indent=2))
    elif args.command == "switch":
        aid, acc = mgr.switch_account(args.account)
        print(json.dumps({"active_account_id": aid, "name": (acc or {}).get("name")}, indent=2))
    elif args.command == "refresh":
        print(json.dumps(mgr.refresh_account_token(args.account), indent=2))


if __name__ == "__main__":
    main()
