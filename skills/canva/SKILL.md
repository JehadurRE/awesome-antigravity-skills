---
name: canva
description: >-
  Universal Canva design and automation skill powered by the Canva Model Context Protocol (MCP).
  Covers creating any Canva format (social posts, carousels, stories, thumbnails, presentations,
  posters, flyers, brochures, reports, magazines, and brand collateral), multi-account OAuth 2.0 PKCE
  rotation, layout grids, typography systems, and optional print/Illustrator prepress handoff.
---

# Canva Universal Design & MCP Automation Skill

This skill equips the agent to design, edit, and export **any type of Canva design** through the **Canva Model Context Protocol (MCP)** (`https://mcp.canva.com/mcp` or the unified `canva-skills-mcp` server), combining automated multi-account OAuth rotation with crisp layout, typography, and print prepress standards.

---

## 1. Canva MCP Integration & Multi-Account OAuth

* **Remote Canva MCP Endpoint:** `https://mcp.canva.com/mcp` (`Accept: application/json, text/event-stream`)
* **OAuth Discovery:** `https://mcp.canva.com/.well-known/oauth-authorization-server`
* **OAuth Endpoints:**
  * Authorize: `https://mcp.canva.com/authorize`
  * Token Exchange / Refresh: `https://mcp.canva.com/token`
  * Dynamic Client Registration (RFC 7591): `https://mcp.canva.com/register`
* **Scopes:** `profile:read design:meta:read design:content:write design:content:read asset:read asset:write folder:read brandkit:read`

> Always exchange authorization codes and refresh tokens against `https://mcp.canva.com/token` rather than `https://api.canva.com/rest/v1/oauth/token` for MCP-scoped credentials.

### Zero-Cooldown Multi-Account Rotation
* Generative calls (`create-design`) consume Canva AI credits and can trigger `quota_cooldown` (typically 180–300 seconds).
* Using `canva-skills-mcp` (`canva_remote_call` / `canva_switch_account`), cooldown errors are caught immediately, `cooldown_ends_at` is recorded, and execution rotates to the next connected Canva account with zero waiting.
* Expired `401` access tokens are automatically refreshed via the account's `refresh_token`.

---

## 2. Core Canva MCP Tools Workflow

1. **Discover Tools & Formats:** Call `canva_remote_discover()` and `canva_get_layout_spec(list_all=true)`.
2. **Prepare Media & Brand Assets:** Use `upload-asset-from-url` / `create-upload-url` and `list-brand-kits` so user logos, product shots, and brand colors are applied faithfully.
3. **Create Designs:** Call `create-design` with a structured brief covering format/dimensions, visual hierarchy, color palette, typography pairing, and exact copy; poll `get-create-design-async-job` until `status == "completed"`.
4. **Refine Precisely:** Use `start-editing-transaction`, `perform-editing-operations` (`replace_text`, `update_fill`, `position_element`), and `commit-editing-transaction`.
5. **Export Deliverables:** Call `export-design` or `create-design-export-job` (`png`, `jpg`, `pdf`, `pptx`, `mp4`).

---

## 3. Universal Layout & Typography Standards

* **Social Media & Video:**
  * Square (`1080×1080 px`), Carousel (`1080×1350 px`), Stories/Reels (`1080×1920 px` with top `250 px` and bottom `300 px` UI-safe zones), YouTube Thumbnails (`1280×720 px`), LinkedIn Banners (`1584×396 px` keeping bottom-left `280 px` clear).
* **Presentations (`1920×1080 px`):**
  * 16:9 widescreen, `72–96 px` safe margins, 1 slide = 1 key takeaway, `>= 18–22 pt` body copy, KPI cards instead of dense paragraphs.
* **Print & Editorial (`8.5"×11"` US Letter / `A4` / `18"×24"` Poster):**
  * Add `0.125"` (`9 pt`) bleed for full-bleed backgrounds; keep all typography, logos, and imagery strictly inside the `36 pt` (`0.5"`) safe margin (`540×720 pt` live area on US Letter).
  * Enforce **`>= 11.0 pt` body copy** (`1.45–1.55` line height) split into 2 or 3 balanced columns (`45–65` characters per line).
* **Color & Contrast:** Follow a 60–30–10 hierarchy with accessible contrast (`>= 4.5:1` for body copy) and max 2–3 complementary fonts.

---

## 4. Optional Print & Adobe Illustrator Prepress Handoff

When converting an approved Canva PDF export into editable Adobe Illustrator masters (`.ai` / `.eps`):
1. Extract embedded fonts from the Canva PDF via `pymupdf` (`doc.extract_font(xref)`) and install them into Adobe/system font directories before opening the PDF.
2. Purge fragmented 1-character glyph text frames from PDF import and reconstruct clean flowing `AreaText` columns and `PointText` headings sourced 100% from the Canva PDF stream (`page.get_text("dict")`).
3. Anchor `PointText` via geometric top (`tf.top = -bbox[1]`, never baseline `origin_y`), add `>= 20 pt` height headroom to `AreaText` frames to eliminate `[+]` overset indicators, and apply `italics = true` on static base fonts for variable-font compatibility.
