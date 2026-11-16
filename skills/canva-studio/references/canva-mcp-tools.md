# Canva MCP Tooling & Workflow Reference

All remote Canva MCP tools can be invoked through `canva_remote_call(tool_name, arguments)` (which automatically refreshes expired tokens and rotates accounts on `quota_cooldown`) or directly via `canva__<tool_name>` when `CANVA_PROXY_REMOTE_TOOLS=1`.

Always run `canva_remote_discover()` once per session to verify the exact live input schemas returned by `https://mcp.canva.com/mcp`.

---

## Core Tool Categories

### 1. Design Creation & Composition
* `create-design` — Generate a new Canva design from a structured prompt / design type (social post, presentation, flyer, poster, brochure, resume, infographic, banner, etc.).
* `get-create-design-async-job` — Poll an async creation job ID until `status == "completed"` and retrieve the created design ID & candidate previews.
* `copy-design` — Duplicate an existing design or template before making campaign/localized variations.
* `merge-designs` — Combine pages from multiple designs into a single unified multi-page deck or publication.
* `get-design` — Fetch design metadata, page count, `edit_url`, `view_url`, and thumbnails.
* `list-designs` / `search-designs` — Locate existing user designs by keyword or folder.

### 2. Interactive Editing Transactions
For surgical post-generation updates without regenerating from scratch:
1. `start-editing-transaction` — Open an edit session on a `design_id` and obtain a `transaction_id` + page element tree.
2. `perform-editing-operations` — Execute structured operations such as `replace_text`, `update_fill`, `position_element`, `resize_element`, or image replacement.
3. `commit-editing-transaction` — Persist all staged edits atomically.

### 3. Assets, Uploads & Brand Kits
* `upload-asset-from-url` — Ingest remote images/logos into the user's Canva media library.
* `create-upload-url` — Obtain a direct upload URL for local image/media binaries.
* `import-design-from-url` — Import external PDF/PPTX/image files as editable Canva designs.
* `list-brand-kits` / `get-brand-kit` — Inspect brand colors, logos, and fonts when aligning designs with an organization's identity.
* `list-folders` — Browse Canva folder hierarchy for organized saving.

### 4. Exporting Final Deliverables
* `export-design` or `create-design-export-job` + `get-design-export-job` — Export finished designs as:
  * **`png` / `jpg`** — Social media posts, web graphics, thumbnails, and visual proofs.
  * **`pdf`** — Standard digital PDFs or print-ready PDFs (`letter`, `a4`, with bleed/crop options).
  * **`pptx`** — Editable PowerPoint slide decks.
  * **`mp4` / `gif`** — Animated social stories, reels, and motion graphics.
