---
name: pptx-presentation-designer
description: >-
  Standardized professional PowerPoint (PPTX) presentation design, typography, layout optimization,
  prepress visual hierarchy, and programmatic automation skill using python-pptx and PowerPoint COM.
  Enforces institutional visual identity, accessible color contrast, modern KPI cards, clean agenda structures,
  and unabridged content integrity.
---

# Professional PPTX Presentation Designer & Optimization Standard

This skill establishes the production standard for auditing, modernizing, and designing high-impact institutional, corporate, and governmental PowerPoint (.pptx) presentations.

---

## 1. Core Principles & Negative Constraints

1. **Preserve Institutional Identity & Brand Integrity:**
   - Always retain official emblems, logos, crests, and watermarks.
   - Maintain the official color palette of the organization while upgrading harsh/raw default colors (e.g. pure `#FF0000` or neon green `#00FF00`) to dignified, accessible hues (e.g. Royal Navy `#0D2340`, Deep Crimson `#8B1E1E`, Emerald `#006A4E`, Gold `#C69214`).
   - Symmetrically pad corner crests (standard 20–28 pt margin from top and sides) rather than letting them touch slide boundaries.

2. **Negative Constraints & Anti-Patterns to Eliminate:**
   - **No Square Bullet Glyphs in Titles**: Eliminate literal `[ ]` (`\u25a1`, `\u25a2`) or raw box outlines around headers.
   - **No Low-Contrast Color Pairings**: Never use red text on blue backgrounds or light green text on light backgrounds.
   - **No 2007-Era Glossy Plastic 3D Gradients**: Replace heavy bevels and gradients with flat, modern, clean-card surfaces with subtle borders (`#E2E8F0`).
   - **No Mismatched Typography**: Enforce a strict 2-font system (e.g. Arial / Calibri or Segoe UI for UI/headings and clean body text). Eliminate arbitrary mixing of Times New Roman, Book Antiqua, and Nikosh on the same slide.
   - **No Trailing Ellipses**: Remove informal `....` or `...` from professional titles.

3. **Content & Unabridged Integrity:**
   - Retain all statistics, center counts, fiscal year steps, durations, partner names, and trainee figures without truncation.
   - Fix obvious grammatical, spelling, and typographical mistakes (e.g. "Bureau Varitus" -> "Bureau Veritas", "Settelite" -> "Satellite").

---

## 2. Standard Layout Archetypes

### Archetype A: Executive Title & Welcome Slides
- Center emblem with balanced white space.
- Dignified typography hierarchy: Organization Name, Directorate, Branch, and Presentation Subtitle.

### Archetype B: Agenda / Scope Roadmap
- Modern numbered grid or card progression (`01`, `02`, `03`...) with subtle status/phase indicators.
- Avoid plain single-box bullet dumps.

### Archetype C: Course / Program Profile Cards
- **Two-Column Split Layout**:
  - **Left Column**: Structured KPI parameter tiles (Accreditation, Centers, Trainee Capacity, FY Steps, Duration).
  - **Right Column**: Framed photographic illustration with rounded corners (`RoundedRectangle`) or subtle borders.

### Archetype D: Data & Metric Comparison Dashboards
- Side-by-side KPI cards with highlighted metrics (Total Trainees, Placed, Self-Employed, Placement Rate %).
- Emphasize key outcomes with contrast badges.

### Archetype E: Modern Tables
- Solid high-contrast header row (e.g. Navy fill `#0D2340` with White bold text `#FFFFFF`).
- Alternating subtle row striping (`#FFFFFF` and `#F8FAFC`).
- Padded cell text with vertical center alignment.

---

## 3. Automation via `python-pptx`

- Use `python-pptx` for in-place modification of existing presentations to preserve embedded media (videos, sound clips, complex vector shapes).
- Shape positioning: calculate exact points (`Pt(x)`) and inches (`Inches(x)`).
- Typography control: assign `font.name`, `font.size`, `font.bold`, and `font.color.rgb = RGBColor(r, g, b)`.
- Re-align images and add container card shapes behind text for high legibility.
