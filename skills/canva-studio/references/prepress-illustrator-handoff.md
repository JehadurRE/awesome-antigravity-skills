# Canva to Adobe Illustrator Prepress Handoff (Option A Standard)

## 1. Pre-Flight Font Extraction & Deployment
Never open or embed a Canva PDF in Adobe Illustrator before installing its embedded fonts:
1. Extract embedded font binaries from the Canva vector PDF using `canva_extract_pdf_fonts` (or `scripts/extract_pdf_prepress.py` via PyMuPDF `doc.extract_font(xref)`).
2. Archive fonts locally in `fonts/` alongside the project deliverables.
3. Deploy fonts to `%APPDATA%\Adobe\Fonts` (Windows) / `~/Library/Application Support/Adobe/Fonts` (macOS) and user system font directories; restart Illustrator if already running so `app.textFonts` re-indexes.

## 2. Option A Live Editable Text Reconstruction
Canva PDF exports split text into disconnected 1-character or single-word `PointText` frames. Option A preserves all background vectors, shapes, and high-resolution images while replacing fragmented text with clean, flowing typography:
1. Open the Canva PDF in Illustrator and switch document color space to **CMYK** (`app.executeMenuCommand('doc-color-cmyk')`).
2. Purge fragmented PDF text frames (`while (doc.textFrames.length > 0) doc.textFrames[0].remove();`).
3. Create a dedicated `"Live Editable Text"` layer above artwork.
4. **Source Integrity:** Extract **100% of text, bounding boxes, font sizes, and colors directly from Canva's PDF stream** (`canva_inspect_pdf` / `page.get_text("dict")`).
5. Typeset body paragraphs into flowing `AreaText` frames (`layer.textFrames.areaText(rect)`).
6. Typeset headlines, labels, metric pairs, and page folios as discrete `PointText` frames.

## 3. ExtendScript Text Frame Physics & Variable Font Fixes
* **Geometric Top Anchoring (`tf.top = -bbox[1]`):** In Illustrator ExtendScript, `PointText.top` sets the **top of the geometric bounding box**, NOT the baseline. Always pass `-bbox[1]` (never `origin_y`) so text does not shift downward into borders.
* **Zero Overset Text (`TOTAL_OVERFLOWS: 0`):** Size every `AreaText` rectangle with vertical clearance:
  $$H \ge (\text{Total Paragraph Lines} \times \text{Leading}) + 20.0\text{ pt}$$
  Deconstruct multi-cell metric cards into discrete coordinate-anchored `PointText` value+label pairs.
* **Variable Font Italic Fix:** ExtendScript silently falls back to `MyriadPro-Regular` when assigned a variable italic TTF (`fvar`/`gvar`). Assign the static upright font and enable `tr.characterAttributes.italics = true;`.

## 4. Recommended 4-Tier Delivery Structure
```text
adobe-illustrator/
├── non-editable/           # Direct Canva PDF master (_Master.ai, _Master.eps)
├── outlined-non-editable/  # Outlined prepress direct Canva version (remText = 0)
├── live-editable/          # Option A human-editable AreaText master (_Master.ai, _Master.eps)
├── outlined-editable/      # Outlined prepress Option A version (remText = 0)
└── fonts/                  # Extracted .ttf / .otf font archive
```
