"""Unified Canva Skills MCP Server (JSON-RPC 2.0 over stdio)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .auth import AccountManager, start_oauth_flow
from .prepress import DESIGN_PRESETS, compute_layout_spec, extract_pdf_fonts, inspect_pdf, list_design_presets
from .remote_proxy import CanvaRemoteClient

SERVER_NAME = "canva-skills-mcp"
SUPPORTED_PROTOCOL_VERSION = "2024-11-05"


def get_skills_root() -> Path:
    env_dir = os.environ.get("CANVA_SKILLS_DIR", "").strip()
    if env_dir:
        return Path(env_dir).expanduser().resolve()
    return Path(__file__).resolve().parent.parent / "skills"


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---"):
        return {}, text
    lines = text.splitlines()
    end_idx = None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            end_idx = idx
            break
    if end_idx is None:
        return {}, text

    meta: dict[str, str] = {}
    current_key: str | None = None
    buf: list[str] = []
    for line in lines[1:end_idx]:
        if ":" in line and not line.startswith((" ", "\t")):
            if current_key is not None:
                meta[current_key] = " ".join(buf).strip()
            k, v = line.split(":", 1)
            current_key = k.strip()
            cleaned = v.strip()
            buf = [] if cleaned in (">-", "|", ">", "|-") else [cleaned]
        elif current_key is not None:
            buf.append(line.strip())
    if current_key is not None:
        meta[current_key] = " ".join(buf).strip()

    body = "\n".join(lines[end_idx + 1 :]).lstrip("\n")
    return meta, body


def discover_skills(skills_root: Path | None = None) -> list[dict[str, Any]]:
    root = skills_root or get_skills_root()
    if not root.exists():
        return []
    skills: list[dict[str, Any]] = []
    for skill_dir in sorted(root.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            continue
        raw = skill_md.read_text(encoding="utf-8")
        meta, _ = _parse_frontmatter(raw)
        refs_dir = skill_dir / "references"
        refs = sorted(p.name for p in refs_dir.glob("*.md")) if refs_dir.exists() else []
        scripts_dir = skill_dir / "scripts"
        scripts = sorted(p.name for p in scripts_dir.glob("*.py")) if scripts_dir.exists() else []
        skills.append(
            {
                "id": skill_dir.name,
                "name": meta.get("name", skill_dir.name),
                "description": meta.get("description", ""),
                "path": str(skill_md),
                "references": refs,
                "scripts": scripts,
            }
        )
    return skills


def _json_result(data: Any) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": json.dumps(data, indent=2)}]}


def _text_result(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def _error_result(message: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": message}], "isError": True}


class UnifiedCanvaMCPServer:
    """Handles MCP protocol requests for universal Canva design skills, OAuth rotation, remote proxy, and prepress."""

    def __init__(
        self,
        skills_root: Path | None = None,
        manager: AccountManager | None = None,
        remote_client: CanvaRemoteClient | None = None,
    ) -> None:
        self.skills_root = skills_root or get_skills_root()
        self.manager = manager or AccountManager()
        self.remote_client = remote_client or CanvaRemoteClient(manager=self.manager)

    def get_tools(self) -> list[dict[str, Any]]:
        tools: list[dict[str, Any]] = [
            {
                "name": "canva_list_skills",
                "description": "List all bundled Canva and design skills along with their reference guides and helper scripts.",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "canva_get_skill",
                "description": "Load the full SKILL.md or a specific reference markdown guide (e.g. 'canva-mcp-tools.md') for a bundled skill.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "skill_id": {
                            "type": "string",
                            "description": "Skill directory name (e.g. 'canva-studio', 'canva', 'pptx-presentation-designer').",
                        },
                        "reference": {
                            "type": "string",
                            "description": "Optional reference filename inside the skill's references/ directory.",
                        },
                    },
                    "required": ["skill_id"],
                },
            },
            {
                "name": "canva_get_layout_spec",
                "description": "Return exact dimensions, safe margins, bleed, grid columns, and typography specs for any Canva design format (social, presentations, posters, reports, magazines, business cards).",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "preset": {
                            "type": "string",
                            "enum": sorted(DESIGN_PRESETS.keys()),
                            "default": "us-letter-3col",
                            "description": "Format preset ID, or omit to use us-letter-3col.",
                        },
                        "list_all": {
                            "type": "boolean",
                            "default": False,
                            "description": "If true, returns a summary list of all supported format presets.",
                        },
                    },
                },
            },
            {
                "name": "canva_list_accounts",
                "description": "List connected Canva MCP OAuth accounts, active account, token readiness, and cooldown status.",
                "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
            },
            {
                "name": "canva_switch_account",
                "description": "Switch the active Canva account to a specific account_id or rotate to the next non-cooled-down account.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "account_id": {
                            "type": "string",
                            "description": "Target account ID (omit to rotate to the next ready account).",
                        }
                    },
                },
            },
            {
                "name": "canva_refresh_token",
                "description": "Refresh the OAuth 2.0 access token for the active or specified Canva account.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "account_id": {"type": "string", "description": "Optional account ID to refresh."}
                    },
                },
            },
            {
                "name": "canva_connect_account",
                "description": "Start a local OAuth 2.0 PKCE authorization flow (with RFC 7591 dynamic client registration if needed) to connect a primary or secondary Canva account.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "account_id": {"type": "string", "default": "account_1"},
                        "name": {"type": "string", "description": "Human-friendly label such as 'Primary Account'."},
                        "port": {"type": "integer", "default": 8080},
                        "open_browser": {"type": "boolean", "default": True},
                        "wait_for_callback": {"type": "boolean", "default": False},
                    },
                },
            },
            {
                "name": "canva_remote_discover",
                "description": "Discover all live tools exposed by the remote Canva MCP server (https://mcp.canva.com/mcp) using the active authenticated account.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "account_id": {"type": "string", "description": "Optional account ID override."}
                    },
                },
            },
            {
                "name": "canva_remote_call",
                "description": "Call any remote Canva MCP tool (create-design, get-create-design-async-job, copy-design, merge-designs, get-design, start-editing-transaction, perform-editing-operations, commit-editing-transaction, upload-asset-from-url, export-design, etc.) with automatic 401 token refresh and zero-wait multi-account rotation on quota_cooldown.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tool_name": {"type": "string", "description": "Remote Canva MCP tool name."},
                        "arguments": {"type": "object", "description": "Tool arguments object."},
                        "account_id": {"type": "string", "description": "Optional starting account ID."},
                        "auto_rotate": {"type": "boolean", "default": True},
                    },
                    "required": ["tool_name"],
                },
            },
            {
                "name": "canva_inspect_pdf",
                "description": "Inspect a Canva-exported PDF using PyMuPDF: verify page dimensions, safe margin compliance, embedded fonts, <11pt spans, and exact bbox coordinates.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string", "description": "Path to exported PDF file."},
                        "max_pages": {"type": "integer", "default": 5},
                        "safe_margin_pt": {"type": "number", "default": 36.0},
                    },
                    "required": ["pdf_path"],
                },
            },
            {
                "name": "canva_extract_pdf_fonts",
                "description": "Extract all embedded TTF/OTF font binaries from a Canva-exported PDF into a target fonts directory for print or Illustrator prepress.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pdf_path": {"type": "string", "description": "Path to exported PDF file."},
                        "output_dir": {"type": "string", "description": "Directory where extracted fonts should be saved."},
                    },
                    "required": ["pdf_path", "output_dir"],
                },
            },
        ]

        if os.environ.get("CANVA_PROXY_REMOTE_TOOLS", "0") == "1":
            try:
                discovered = self.remote_client.list_tools()
                remote_tools = discovered.get("response", {}).get("result", {}).get("tools", [])
                for rt in remote_tools:
                    if isinstance(rt, dict) and rt.get("name"):
                        tools.append(
                            {
                                "name": f"canva__{rt['name']}",
                                "description": f"[Canva Remote Proxy] {rt.get('description', '')}".strip(),
                                "inputSchema": rt.get("inputSchema", {"type": "object", "properties": {}}),
                            }
                        )
            except Exception:
                pass

        return tools

    def get_resources(self) -> list[dict[str, Any]]:
        resources: list[dict[str, Any]] = []
        for skill in discover_skills(self.skills_root):
            sid = skill["id"]
            resources.append(
                {
                    "uri": f"skill://{sid}/SKILL.md",
                    "name": f"{sid} — SKILL.md",
                    "description": skill["description"],
                    "mimeType": "text/markdown",
                }
            )
            for ref in skill["references"]:
                resources.append(
                    {
                        "uri": f"skill://{sid}/references/{ref}",
                        "name": f"{sid}/{ref}",
                        "description": f"Reference guide {ref} for {sid}",
                        "mimeType": "text/markdown",
                    }
                )
        return resources

    def read_resource(self, uri: str) -> dict[str, Any]:
        if not uri.startswith("skill://"):
            raise ValueError(f"Unsupported resource URI: {uri}")
        rel = uri[len("skill://") :].lstrip("/")
        target = (self.skills_root / rel).resolve()
        if not str(target).startswith(str(self.skills_root.resolve())) or not target.exists():
            raise FileNotFoundError(f"Resource not found: {uri}")
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "text/markdown",
                    "text": target.read_text(encoding="utf-8"),
                }
            ]
        }

    def get_prompts(self) -> list[dict[str, Any]]:
        return [
            {
                "name": "canva-create-design",
                "description": "Create any type of Canva design (social post, pitch deck, poster, flyer, brochure, resume, report, or brand asset) via Canva MCP.",
                "arguments": [
                    {"name": "format", "description": "Design format (e.g. instagram_post, presentation, poster, magazine, flyer, logo)", "required": True},
                    {"name": "brief", "description": "Design topic, audience, brand style, and copy/content requirements", "required": True},
                ],
            },
            {
                "name": "canva-social-campaign",
                "description": "Generate a cohesive multi-format social campaign (square feed, 4:5 carousel, 9:16 story) with consistent typography and color palette.",
                "arguments": [
                    {"name": "campaign_topic", "description": "Campaign theme or product announcement", "required": True},
                    {"name": "brand_colors", "description": "Optional hex palette", "required": False},
                ],
            },
            {
                "name": "canva-presentation-deck",
                "description": "Build a clean 16:9 presentation or pitch deck in Canva with strong visual hierarchy and KPI slides.",
                "arguments": [
                    {"name": "topic", "description": "Deck title and objective", "required": True},
                    {"name": "slide_count", "description": "Target number of slides", "required": False},
                ],
            },
            {
                "name": "canva-editorial-publication",
                "description": "Design a multi-page report, magazine, whitepaper, or policy brief with safe print margins and >=11pt body typography.",
                "arguments": [
                    {"name": "topic", "description": "Publication title or subject", "required": True},
                    {"name": "preset", "description": "us-letter-3col, us-letter-2col, or a4-editorial", "required": False},
                ],
            },
            {
                "name": "canva-to-illustrator-prepress",
                "description": "Inspect an exported Canva PDF, extract embedded fonts, and prepare Option A live-editable Illustrator files.",
                "arguments": [
                    {"name": "pdf_path", "description": "Path to exported Canva PDF", "required": True},
                ],
            },
        ]

    def get_prompt(self, name: str, arguments: dict[str, str] | None = None) -> dict[str, Any]:
        args = arguments or {}
        templates = {
            "canva-create-design": (
                f"Load `canva_get_skill(skill_id='canva-studio')` and discover available remote tools with "
                f"`canva_remote_discover()`. Design a '{args.get('format', 'custom')}' in Canva using "
                f"`canva_remote_call(tool_name='create-design', ...)` following this brief: {args.get('brief', '')}. "
                f"Poll the async job until completed, inspect/refine with editing transactions if needed, and export proofs."
            ),
            "canva-social-campaign": (
                f"Load `canva_get_skill(skill_id='canva-studio', reference='design-formats-and-grids.md')`. "
                f"Create a cohesive social campaign for '{args.get('campaign_topic', '')}' "
                f"(palette: {args.get('brand_colors', 'harmonious high-contrast editorial')}) across social-square, "
                f"social-portrait, and story-reel safe zones via `canva_remote_call`."
            ),
            "canva-presentation-deck": (
                f"Load `canva_get_layout_spec(preset='presentation-16x9')` and `canva_get_skill(skill_id='canva-studio')`. "
                f"Create a {args.get('slide_count', '10')}-slide 16:9 Canva presentation on '{args.get('topic', '')}' "
                f"with crisp visual hierarchy, safe margins, and scannable KPI/agenda layouts."
            ),
            "canva-editorial-publication": (
                f"Load `canva_get_layout_spec(preset='{args.get('preset', 'us-letter-3col')}')` and "
                f"`canva_get_skill(skill_id='canva-studio')`. Create a print-ready publication on "
                f"'{args.get('topic', '')}' strictly inside the safe margins with >=11pt body typography."
            ),
            "canva-to-illustrator-prepress": (
                f"Run `canva_inspect_pdf` and `canva_extract_pdf_fonts` on '{args.get('pdf_path', '')}', "
                f"then follow `canva_get_skill(skill_id='canva-studio', reference='prepress-illustrator-handoff.md')` "
                f"to produce clean live-editable and outlined prepress deliverables."
            ),
        }
        if name not in templates:
            raise KeyError(f"Unknown prompt: {name}")
        return {
            "description": name,
            "messages": [{"role": "user", "content": {"type": "text", "text": templates[name]}}],
        }

    def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        args = arguments or {}
        try:
            if name == "canva_list_skills":
                return _json_result({"skills_root": str(self.skills_root), "skills": discover_skills(self.skills_root)})

            if name == "canva_get_skill":
                skill_id = str(args["skill_id"]).strip()
                skill_dir = (self.skills_root / skill_id).resolve()
                if not str(skill_dir).startswith(str(self.skills_root.resolve())) or not skill_dir.is_dir():
                    return _error_result(f"Unknown skill_id '{skill_id}'.")
                ref = args.get("reference")
                if ref:
                    target = (skill_dir / "references" / str(ref)).resolve()
                    if not str(target).startswith(str(skill_dir)) or not target.exists():
                        return _error_result(f"Reference '{ref}' not found in '{skill_id}'.")
                    return _text_result(target.read_text(encoding="utf-8"))
                skill_md = skill_dir / "SKILL.md"
                if not skill_md.exists():
                    return _error_result(f"SKILL.md missing for '{skill_id}'.")
                return _text_result(skill_md.read_text(encoding="utf-8"))

            if name == "canva_get_layout_spec":
                if args.get("list_all"):
                    return _json_result({"presets": list_design_presets()})
                preset = str(args.get("preset") or "us-letter-3col")
                return _json_result(compute_layout_spec(preset))

            if name == "canva_list_accounts":
                return _json_result(self.manager.list_accounts())

            if name == "canva_switch_account":
                aid, acc = self.manager.switch_account(args.get("account_id"))
                return _json_result(
                    {"active_account_id": aid, "name": (acc or {}).get("name"), "status": "switched"}
                )

            if name == "canva_refresh_token":
                return _json_result(self.manager.refresh_account_token(args.get("account_id")))

            if name == "canva_connect_account":
                return _json_result(
                    start_oauth_flow(
                        account_id=str(args.get("account_id", "account_1")),
                        name=args.get("name"),
                        port=args.get("port"),
                        open_browser=bool(args.get("open_browser", True)),
                        wait_for_callback=bool(args.get("wait_for_callback", False)),
                        manager=self.manager,
                    )
                )

            if name == "canva_remote_discover":
                return _json_result(self.remote_client.list_tools(account_id=args.get("account_id")))

            if name == "canva_remote_call":
                return _json_result(
                    self.remote_client.call_tool(
                        tool_name=str(args["tool_name"]),
                        arguments=args.get("arguments") or {},
                        account_id=args.get("account_id"),
                        auto_rotate=bool(args.get("auto_rotate", True)),
                    )
                )

            if name.startswith("canva__"):
                remote_tool = name[len("canva__") :]
                return _json_result(self.remote_client.call_tool(remote_tool, args))

            if name == "canva_inspect_pdf":
                return _json_result(
                    inspect_pdf(
                        str(args["pdf_path"]),
                        max_pages=int(args.get("max_pages", 5)),
                        safe_margin_pt=float(args.get("safe_margin_pt", 36.0)),
                    )
                )

            if name == "canva_extract_pdf_fonts":
                return _json_result(extract_pdf_fonts(str(args["pdf_path"]), str(args["output_dir"])))

            return _error_result(f"Unknown tool: {name}")
        except Exception as exc:
            return _error_result(f"{type(exc).__name__}: {exc}")

    def handle_request(self, req: dict[str, Any]) -> dict[str, Any] | None:
        req_id = req.get("id")
        method = req.get("method", "")
        params = req.get("params") or {}

        if req_id is None and method.startswith("notifications/"):
            return None

        try:
            if method == "initialize":
                client_proto = params.get("protocolVersion") or SUPPORTED_PROTOCOL_VERSION
                result = {
                    "protocolVersion": client_proto,
                    "capabilities": {
                        "tools": {"listChanged": False},
                        "resources": {"subscribe": False, "listChanged": False},
                        "prompts": {"listChanged": False},
                    },
                    "serverInfo": {"name": SERVER_NAME, "version": __version__},
                }
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = {"tools": self.get_tools()}
            elif method == "tools/call":
                result = self.call_tool(params.get("name", ""), params.get("arguments"))
            elif method == "resources/list":
                result = {"resources": self.get_resources()}
            elif method == "resources/read":
                result = self.read_resource(params.get("uri", ""))
            elif method == "prompts/list":
                result = {"prompts": self.get_prompts()}
            elif method == "prompts/get":
                result = self.get_prompt(params.get("name", ""), params.get("arguments"))
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                }
            return {"jsonrpc": "2.0", "id": req_id, "result": result}
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32000, "message": str(exc)},
            }


def run_stdio_server(server: UnifiedCanvaMCPServer | None = None) -> None:
    """Run the MCP JSON-RPC 2.0 server over stdin/stdout (supports NDJSON and Content-Length framing)."""
    srv = server or UnifiedCanvaMCPServer()
    stdin_buf = sys.stdin.buffer
    stdout_buf = sys.stdout.buffer

    while True:
        line = stdin_buf.readline()
        if not line:
            break

        stripped = line.strip()
        if not stripped:
            continue

        use_content_length = False
        if stripped.lower().startswith(b"content-length:"):
            use_content_length = True
            length = int(stripped.split(b":", 1)[1].strip())
            while True:
                header_line = stdin_buf.readline()
                if not header_line or header_line.strip() == b"":
                    break
            body_bytes = stdin_buf.read(length)
            raw_msg = body_bytes.decode("utf-8")
        else:
            raw_msg = stripped.decode("utf-8")

        try:
            req = json.loads(raw_msg)
        except json.JSONDecodeError:
            continue

        resp = srv.handle_request(req)
        if resp is None:
            continue

        encoded = json.dumps(resp, ensure_ascii=False).encode("utf-8")
        if use_content_length:
            frame = f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii") + encoded
            stdout_buf.write(frame)
        else:
            stdout_buf.write(encoded + b"\n")
        stdout_buf.flush()
