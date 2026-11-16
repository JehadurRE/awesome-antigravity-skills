"""Prepress PDF font extractor and text bounding-box inspector for Canva -> Illustrator Option A."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from mcp_server.prepress import extract_pdf_fonts, inspect_pdf  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect Canva PDFs and extract embedded fonts for Illustrator prepress")
    sub = parser.add_subparsers(dest="command", required=True)

    insp = sub.add_parser("inspect", help="Inspect page trim, safe margins, fonts, and text bounding boxes")
    insp.add_argument("pdf_path", help="Path to exported Canva PDF")
    insp.add_argument("--max-pages", type=int, default=5)

    ext = sub.add_parser("extract-fonts", help="Extract embedded TTF/OTF font streams from Canva PDF")
    ext.add_argument("pdf_path", help="Path to exported Canva PDF")
    ext.add_argument("--out", default="./adobe illustrator/fonts", help="Destination fonts directory")

    args = parser.parse_args()
    if args.command == "inspect":
        print(json.dumps(inspect_pdf(args.pdf_path, max_pages=args.max_pages), indent=2))
    elif args.command == "extract-fonts":
        print(json.dumps(extract_pdf_fonts(args.pdf_path, args.out), indent=2))


if __name__ == "__main__":
    main()
