---
name: canva-studio
description: >-
  Unified Canva MCP & universal design studio skill for creating any type of Canva design
  (social media posts & carousels, stories/reels, YouTube thumbnails, pitch decks & presentations,
  posters, flyers, brochures, resumes, reports, magazines, and brand collateral) using Canva MCP,
  multi-account OAuth 2.0 rotation, responsive layout grids, typography systems, and optional
  print/Illustrator prepress handoff.
---

# Canva Studio — Unified Canva MCP & Universal Design System

This skill equips any agent with end-to-end **Canva Model Context Protocol (MCP)** automation and senior visual design mastery to create **any type of Canva design**—from social graphics and pitch decks to posters, marketing collateral, and multi-page print publications.

---

## 1. Unified MCP Capabilities

When connected to `canva-skills-mcp` (`python -m mcp_server`), you have unified access to:

| Capability | MCP Tool(s) | Purpose |
| :--- | :--- | :--- |
| **Account Auth & Rotation** | `canva_connect_account`, `canva_list_accounts`, `canva_switch_account`, `canva_refresh_token` | OAuth 2.0 PKCE + RFC 7591 registration, token refresh, zero-cooldown multi-account switching |
| **Remote Canva MCP Proxy** | `canva_remote_discover`, `canva_remote_call` | Calls `https://mcp.canva.com/mcp` tools (`create-design`, `get-design`, `export-design`, editing transactions, assets, folders, brand kits) with auto `401` refresh & `quota_cooldown` rotation |
| **Format & Grid Specs** | `canva_get_layout_spec`, `canva_list_skills`, `canva_get_skill` | Dimensions, safe zones, bleed, columns, and typography scales for social, video, presentations, print, and brand assets |
| **Print & Prepress Audit** | `canva_inspect_pdf`, `canva_extract_pdf_fonts` | Inspect exported Canva PDFs for safe-margin violations, `<11 pt` copy, exact bbox coordinates, and extract embedded fonts |

---

## 2. Universal Design Creation Workflow (Any Canva Format)

1. **Ensure Authentication:**
   - Check connected accounts via `canva_list_accounts`.
   - If none are connected, call `canva_connect_account(account_id="account_1")` and present the authorization URL. Optionally connect `account_2` for zero-cooldown generation.
2. **Discover Available Tools & Target Specs:**
   - Run `canva_remote_discover()` to verify live remote Canva MCP tool schemas.
   - Run `canva_get_layout_spec(list_all=true)` or `canva_get_layout_spec(preset="...")` to pull exact dimensions and safe margins for the requested design type.
3. **Upload / Stage Brand & Media Assets (If Provided):**
   - Use `upload-asset-from-url` or `create-upload-url` via `canva_remote_call` so real logos, product photos, or portraits are embedded cleanly.
4. **Generate & Poll the Design (`create-design`):**
   - Craft a structured prompt specifying:
     - **Format & Aspect Ratio:** e.g. `1080×1080` square, `1080×1350` 4:5 carousel, `1920×1080` 16:9 deck, `8.5"×11"` US Letter, `A4`, `18"×24"` poster.
     - **Visual Hierarchy & Grid:** Clear focal anchor, balanced whitespace, safe-zone clearance, max 2–3 font families, high-contrast foreground/background pairing.
     - **Exact Copy Integrity:** Include exact headlines, subheads, metrics, CTAs, or body copy without hallucinating unrequested claims.
   - Poll `get-create-design-async-job` until `status == "completed"`.
5. **Inspect & Programmatically Refine (`start-editing-transaction`):**
   - Retrieve design metadata and edit/view URLs via `get-design`.
   - When precise text, fill color, or element adjustments are needed, open an editing transaction (`start-editing-transaction` → `perform-editing-operations` → `commit-editing-transaction`).
6. **Export Deliverables (`export-design` / `create-design-export-job`):**
   - Export `png` / `jpg` for social & web proofs, `pptx` for slide decks, `mp4` for animated/video designs, or print-ready `pdf` for print collateral.

---

## 3. Format Reference Router

Load only the reference guide relevant to the current task:

| Topic | Reference File | Covers |
| :--- | :--- | :--- |
| **Canva MCP Tooling** | [canva-mcp-tools.md](./references/canva-mcp-tools.md) | Design creation, async job polling, editing transactions, asset uploads, brand kits, exports |
| **Format Presets & Grids** | [design-formats-and-grids.md](./references/design-formats-and-grids.md) | Social media, YouTube/LinkedIn, 16:9 pitch decks, posters, business cards, US Letter & A4 editorial grids |
| **Typography & Color** | [typography-and-color-systems.md](./references/typography-and-color-systems.md) | Font pairings across styles (editorial, modern SaaS, bold campaign, luxury), contrast & `>= 11pt` print rules |
| **Multi-Account OAuth** | [oauth-multi-account.md](./references/oauth-multi-account.md) | PKCE OAuth 2.0, RFC 7591 registration, token refresh, zero-cooldown rotation |
| **Print & Illustrator Prepress** | [prepress-illustrator-handoff.md](./references/prepress-illustrator-handoff.md) | Optional Canva PDF → Illustrator font extraction, `AreaText` live reconstruction, `tf.top = -bbox[1]` |

---

## 4. Bundled CLI Helper Scripts

* `scripts/connect_account.py` — Standalone OAuth 2.0 PKCE wizard (`python scripts/connect_account.py --account account_1`).
* `scripts/account_manager.py` — CLI for listing, switching, and refreshing connected Canva accounts.
* `scripts/extract_pdf_prepress.py` — Inspect exported Canva PDFs and extract embedded fonts via PyMuPDF.
