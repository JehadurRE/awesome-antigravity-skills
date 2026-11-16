# Universal Canva Design Formats, Safe Zones & Grid Systems

Use `canva_get_layout_spec(preset=...)` to fetch machine-readable coordinates for any preset below.

---

## 1. Social Media & Video Formats (`px`)

| Preset ID | Format | Dimensions | Safe Margin Notes |
| :--- | :--- | :--- | :--- |
| `social-square` | Instagram / Square Post (`1:1`) | `1080 × 1080 px` | `72 px` all-around margin (`936 × 936 px` live area) |
| `social-portrait` | Feed & Carousel (`4:5`) | `1080 × 1350 px` | `84 px` top/bottom, `72 px` sides (`936 × 1182 px` live area) |
| `story-reel` | Story / Reel / TikTok (`9:16`) | `1080 × 1920 px` | Keep top `250 px` and bottom `300 px` free of critical text/CTAs so platform UI never covers them |
| `youtube-thumbnail` | YouTube Thumbnail (`16:9`) | `1280 × 720 px` | Keep bottom-right corner clear of duration badge; use `<= 4–6` punchy words |
| `linkedin-banner` | LinkedIn Cover Banner | `1584 × 396 px` | Keep bottom-left `280 px` clear for profile avatar overlap |

### Carousel & Social Design Rules
* Maintain **1 clear focal point** per frame (subject or bold headline + supporting visual).
* Leave generous breathing room (`25–35%` open canvas/whitespace).
* Keep swipeable carousels visually anchored with consistent header/footer positions and slide indicators (`01 / 07`).

---

## 2. Presentations & Pitch Decks (`px`)

| Preset ID | Format | Dimensions | Safe Margin & Grid |
| :--- | :--- | :--- | :--- |
| `presentation-16x9` | Widescreen Slide Deck (`16:9`) | `1920 × 1080 px` | `72 px` top/bottom, `96 px` left/right (`1728 × 936 px` live area); 12-column grid (`122 px` cols, `24 px` gutters) |

### Slide Design Rules
* **One Core Idea Per Slide:** Avoid dense paragraphs; convert prose into KPI cards, comparison matrices, timelines, or 2-column visual/text splits.
* **Readable From Across the Room:** Keep body text `>= 18–22 pt`, section headers `24–30 pt`, and slide titles `40–54 pt`.

---

## 3. Print, Editorial & Brand Collateral (`pt` / `in` / `mm`)

| Preset ID | Format | Trim Dimensions | Bleed & Safe Margin | Grid System |
| :--- | :--- | :--- | :--- | :--- |
| `us-letter-3col` | US Letter Magazine / Report | `8.5" × 11"` (`612 × 792 pt`) | `9 pt` (`0.125"`) bleed; `36 pt` (`0.5"`) safe margin (`540 × 720 pt` live) | 3 columns: `168 pt` width, `18 pt` gutters |
| `us-letter-2col` | Policy Brief / Whitepaper | `8.5" × 11"` (`612 × 792 pt`) | `9 pt` bleed; `36 pt` safe margin (`540 × 720 pt` live) | Asymmetric 2-col (`300 pt` narrative + `222 pt` callouts, `18 pt` gutter) |
| `a4-editorial` | A4 Brochure / Document | `210 × 297 mm` (`595.28 × 841.89 pt`) | `8.5 pt` (`3 mm`) bleed; `36 pt` safe margin | 2 equal columns (`252.64 pt` width, `18 pt` gutter) |
| `poster-18x24` | Event / Promotional Poster | `18" × 24"` (`1296 × 1728 pt`) | `9 pt` bleed; `54 pt` (`0.75"`) safe margin | Focal visual + top hook + bottom date/venue/QR anchor |
| `business-card` | US Business Card | `3.5" × 2.0"` (`252 × 144 pt`) | `9 pt` bleed; `14.4 pt` (`0.2"`) safe margin | Minimalist front mark + clean back contact hierarchy (`>= 8–9 pt`) |

### Print Safety Rules
* Only full-bleed background fills, tints, or edge-to-edge imagery extend into the bleed margin.
* **Zero text, logos, QR codes, or borders** may touch or cross the safe margin line.
* For long-form reading on Letter/A4 pages, keep body copy **`>= 11.0 pt`** across multi-column measures (`45–65` characters per line).
