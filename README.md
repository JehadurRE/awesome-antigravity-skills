# Awesome Antigravity Skills — Unified Canva Studio & MCP

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://www.python.org/)
[![MCP Compatible](https://img.shields.io/badge/MCP-JSON--RPC%202.0-10B981.svg)](https://modelcontextprotocol.io/)
[![Zero Core Dependencies](https://img.shields.io/badge/Core%20Deps-Zero%20(Stdlib)-0EA5E9.svg)](#installation)

A unified, open-source **Canva Skills MCP Server** paired with **Antigravity Skills** so anyone can design, edit, and export **any kind of Canva design** (social media posts & carousels, stories/reels, YouTube thumbnails, 16:9 pitch decks, posters, flyers, brochures, reports, resumes, and brand collateral) using **Canva MCP** with zero-cooldown multi-account OAuth rotation.

---

## Why This Exists

Out of the box, remote Canva MCP integrations require manual single-account auth and stall for 3–5 minutes whenever an account hits Canva's AI credit `quota_cooldown`. And creating great designs across formats requires consistent safe zones, aspect ratios, typography scales, and export workflows.

**`awesome-antigravity-skills`** unifies everything into one zero-dependency Python package + Antigravity plugin:

1. **Unified Canva Skills MCP Server (`mcp_server`)**:
   - **Create Any Canva Design via Remote Proxy:** Proxies all tools on `https://mcp.canva.com/mcp` (`create-design`, `get-create-design-async-job`, `copy-design`, `merge-designs`, `get-design`, `start-editing-transaction`, `perform-editing-operations`, `commit-editing-transaction`, `upload-asset-from-url`, `export-design`, brand kits, folders).
   - **Zero-Wait Multi-Account Rotation:** Automatically detects `quota_cooldown` from Canva MCP, records `cooldown_ends_at`, rotates to the next connected Canva account, and retries immediately.
   - **Automatic OAuth 2.0 PKCE + RFC 7591 Dynamic Registration:** Connect one or multiple Canva accounts out of the box with no hardcoded client secrets. Automatically refreshes expired `401` tokens.
   - **Format Presets, Skills & Resources Over MCP:** Provides exact dimensions, safe zones, bleed, grids, and font pairings for social, video, presentations, print, and brand assets via `canva_get_layout_spec` and `skill://...` resources.
   - **Optional Print & Prepress PDF Inspector:** Inspects Canva-exported PDFs for safe-margin violations, `<11 pt` print text, exact Illustrator `tf.top = -bbox[1]` coordinates, and extracts embedded TTF/OTF fonts (via optional `pymupdf`).
2. **Modular Antigravity Skills (`skills/`)**:
   - Drop directly into `~/.gemini/config/skills/`, `.agents/skills/`, or load as a complete Antigravity plugin (`plugin.json` + `mcp_config.json`).

---

## Repository Structure

```text
awesome-antigravity-skills/
├── plugin.json                     # Antigravity plugin manifest
├── mcp_config.json                 # Plugin MCP server definition
├── mcp_config.example.json         # Drop-in MCP config for Antigravity / Claude / Cursor
├── pyproject.toml                  # Installable `canva-skills-mcp` package (stdlib core)
├── .env.example                    # Optional OAuth & state directory settings
├── mcp_server/                     # Unified Canva Skills MCP Server
│   ├── server.py                   # JSON-RPC 2.0 stdio MCP server (Tools, Resources, Prompts)
│   ├── auth.py                     # OAuth 2.0 PKCE, RFC 7591 registration & multi-account manager
│   ├── remote_proxy.py             # Canva remote MCP proxy + 401 refresh + cooldown rotation
│   ├── prepress.py                 # Multi-format geometry presets & PyMuPDF PDF/font inspector
│   └── __main__.py                 # CLI + MCP stdio entrypoint
├── skills/
│   ├── canva-studio/               # Unified Canva MCP & Universal Design Studio skill
│   │   ├── SKILL.md
│   │   ├── references/             # Canva MCP tools, formats/grids, typography/colors, OAuth, prepress
│   │   └── scripts/                # Portable OAuth, account rotation & prepress CLIs
│   ├── canva/                      # Standalone Canva MCP & Multi-Format Design skill
│   └── pptx-presentation-designer/ # Institutional & Corporate PPTX Presentation Design skill
├── scripts/
│   ├── install.ps1                 # Windows PowerShell skills installer
│   └── install.sh                  # macOS/Linux Bash skills installer
└── tests/                          # Automated unit & skill-hygiene validation tests
```

---

## Bundled Skills Catalog

| Skill | Focus | Highlights |
| :--- | :--- | :--- |
| **[`canva-studio`](skills/canva-studio/SKILL.md)** | Unified Canva MCP & Universal Design Studio | Create any Canva design format, multi-account rotation, progressive `references/` & `scripts/` |
| **[`canva`](skills/canva/SKILL.md)** | Standalone Canva Design & MCP Skill | Self-contained `SKILL.md` for Canva MCP workflows, social/deck/print formats & prepress |
| **[`pptx-presentation-designer`](skills/pptx-presentation-designer/SKILL.md)** | PowerPoint Engineering | `python-pptx` KPI cards, modern tables, contrast & brand preservation |

---

## Installation

### 1. Clone the Repository
```bash
git clone https://github.com/JehadurRE/awesome-antigravity-skills.git
cd awesome-antigravity-skills
```

Optional prepress PDF inspection support (`pymupdf`):
```bash
pip install -e ".[prepress]"
```
> **Note:** The core MCP server and OAuth manager require **zero third-party packages** (Python 3.10+ standard library only).

### 2. Install Skills into Antigravity
**Windows (PowerShell):**
```powershell
.\scripts\install.ps1
```

**macOS / Linux:**
```bash
./scripts/install.sh
```

### 3. Register the Unified MCP Server
Add `canva-skills-mcp` to your Antigravity `~/.gemini/config/mcp_config.json` (or Claude Desktop / Cursor MCP config):

```json
{
  "mcpServers": {
    "canva-skills-mcp": {
      "command": "python",
      "args": ["-m", "mcp_server"],
      "cwd": "/ABSOLUTE/PATH/TO/awesome-antigravity-skills",
      "env": {
        "CANVA_STATE_DIR": "~/.canva-skills-mcp"
      }
    }
  }
}
```

> Set `"CANVA_PROXY_REMOTE_TOOLS": "1"` in `env` if you also want remote Canva MCP tools (`canva__create-design`, etc.) mirrored directly in `tools/list` on startup.

---

## Connecting Your Canva Accounts (Zero-Cooldown Rotation)

Connect your primary account (uses RFC 7591 dynamic client registration automatically, or your `CANVA_CLIENT_ID` / `CANVA_CLIENT_SECRET` env vars):

```bash
python -m mcp_server --connect account_1 --name "Primary Canva"
```

Connect a second Canva account (open the printed URL in an Incognito/private window to sign into your second Canva account):

```bash
python -m mcp_server --connect account_2 --name "Secondary Canva" --no-browser
```

Inspect or rotate accounts anytime:
```bash
python -m mcp_server --accounts
python -m mcp_server --switch
```

Or ask your AI agent directly using the `canva_connect_account`, `canva_list_accounts`, and `canva_switch_account` MCP tools!

---

## MCP Tools, Resources & Prompts Reference

### Tools
* **Skills & Format Presets:** `canva_list_skills`, `canva_get_skill`, `canva_get_layout_spec` (`social-square`, `social-portrait`, `story-reel`, `youtube-thumbnail`, `linkedin-banner`, `presentation-16x9`, `us-letter-3col`, `us-letter-2col`, `a4-editorial`, `poster-18x24`, `business-card`)
* **OAuth & Multi-Account Rotation:** `canva_connect_account`, `canva_list_accounts`, `canva_switch_account`, `canva_refresh_token`
* **Remote Canva Proxy:** `canva_remote_discover`, `canva_remote_call`
* **Prepress PDF Inspection:** `canva_inspect_pdf`, `canva_extract_pdf_fonts`

### MCP Resources
All `SKILL.md` and `references/*.md` files are exposed as `skill://<skill-id>/SKILL.md` and `skill://<skill-id>/references/<file>.md`.

### MCP Prompts
* `canva-create-design`
* `canva-social-campaign`
* `canva-presentation-deck`
* `canva-editorial-publication`
* `canva-to-illustrator-prepress`

---

## Running Tests

```bash
python -m unittest discover -s tests -v
```

---

## License

MIT © [JehadurRE](https://github.com/JehadurRE)
