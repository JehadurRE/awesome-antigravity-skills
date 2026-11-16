"""Portable OAuth 2.0 PKCE onboarding wizard for connecting Canva MCP accounts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mcp_server.auth import start_oauth_flow  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Connect a Canva account to Canva Skills MCP via OAuth 2.0 PKCE")
    parser.add_argument("--account", default="account_1", help="Account identifier (e.g. account_1, account_2)")
    parser.add_argument("--name", default=None, help="Human-readable account label")
    parser.add_argument("--port", type=int, default=8080, help="Localhost callback port (default: 8080)")
    parser.add_argument("--no-browser", action="store_true", help="Print the auth URL without launching a browser")
    args = parser.parse_args()

    result = start_oauth_flow(
        account_id=args.account,
        name=args.name,
        port=args.port,
        open_browser=not args.no_browser,
        wait_for_callback=True,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
