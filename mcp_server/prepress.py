"""Universal Canva design format presets, layout geometry specs, and PyMuPDF prepress helpers."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

LETTER_WIDTH_PT = 612.0
LETTER_HEIGHT_PT = 792.0
SAFE_MARGIN_PT = 36.0
BLEED_PT = 9.0

DESIGN_PRESETS: dict[str, dict[str, Any]] = {
    "social-square": {
        "category": "Social Media",
        "name": "Instagram / Square Post (1:1)",
        "unit": "px",
        "dimensions": {"width": 1080, "height": 1080},
        "safe_margin": {"top": 72, "right": 72, "bottom": 72, "left": 72},
        "live_area": {"width": 936, "height": 936},
        "recommended_typography": {"headline_pt": "56-84", "subhead_pt": "28-36", "body_min_pt": "24-30"},
        "canva_design_type": "instagram_post",
    },
    "social-portrait": {
        "category": "Social Media",
        "name": "Instagram / LinkedIn Portrait Feed & Carousel (4:5)",
        "unit": "px",
        "dimensions": {"width": 1080, "height": 1350},
        "safe_margin": {"top": 84, "right": 72, "bottom": 84, "left": 72},
        "live_area": {"width": 936, "height": 1182},
        "recommended_typography": {"headline_pt": "56-88", "subhead_pt": "28-38", "body_min_pt": "24-32"},
        "canva_design_type": "instagram_post",
    },
    "story-reel": {
        "category": "Social Media",
        "name": "Story / Reel / TikTok Vertical (9:16)",
        "unit": "px",
        "dimensions": {"width": 1080, "height": 1920},
        "safe_margin": {"top": 250, "right": 72, "bottom": 300, "left": 72},
        "live_area": {"width": 936, "height": 1370},
        "notes": "Top 250px and bottom 300px reserved clear of platform UI overlays.",
        "canva_design_type": "instagram_story",
    },
    "youtube-thumbnail": {
        "category": "Video & Web",
        "name": "YouTube Thumbnail (16:9)",
        "unit": "px",
        "dimensions": {"width": 1280, "height": 720},
        "safe_margin": {"top": 56, "right": 64, "bottom": 56, "left": 64},
        "live_area": {"width": 1152, "height": 608},
        "notes": "Keep bottom-right corner clear of video timestamp badge.",
        "canva_design_type": "youtube_thumbnail",
    },
    "linkedin-banner": {
        "category": "Social Media",
        "name": "LinkedIn Company / Profile Cover Banner",
        "unit": "px",
        "dimensions": {"width": 1584, "height": 396},
        "safe_margin": {"top": 36, "right": 64, "bottom": 36, "left": 280},
        "live_area": {"width": 1240, "height": 324},
        "notes": "Left 280px kept clear for profile avatar overlap on desktop/mobile.",
        "canva_design_type": "linkedin_banner",
    },
    "presentation-16x9": {
        "category": "Presentations",
        "name": "Widescreen Pitch Deck / Presentation (16:9)",
        "unit": "px",
        "dimensions": {"width": 1920, "height": 1080},
        "safe_margin": {"top": 72, "right": 96, "bottom": 72, "left": 96},
        "live_area": {"width": 1728, "height": 936},
        "columns_12": {"gutter_px": 24, "column_width_px": 122},
        "recommended_typography": {"slide_title_pt": "40-54", "section_pt": "24-30", "body_min_pt": "18-22"},
        "canva_design_type": "presentation",
    },
    "us-letter-3col": {
        "category": "Editorial & Print",
        "name": "US Letter Editorial 3-Column Magazine / Report (8.5 x 11 in)",
        "unit": "pt",
        "dimensions": {"width": 612.0, "height": 792.0, "inches": [8.5, 11.0]},
        "bleed_per_side_pt": BLEED_PT,
        "safe_margin_pt": SAFE_MARGIN_PT,
        "live_area": {"width": 540.0, "height": 720.0, "bounds_pdf": [36.0, 36.0, 576.0, 756.0]},
        "grid": {
            "gutter_pt": 18.0,
            "column_width_pt": 168.0,
            "columns": [
                {"index": 1, "x_start_pt": 36.0, "x_end_pt": 204.0, "width_pt": 168.0},
                {"index": 2, "x_start_pt": 222.0, "x_end_pt": 390.0, "width_pt": 168.0},
                {"index": 3, "x_start_pt": 408.0, "x_end_pt": 576.0, "width_pt": 168.0},
            ],
        },
        "recommended_typography": {"hero_pt": "32-44", "h2_pt": "16-19", "body_min_pt": 11.0, "leading_pt": "14.5-17.0"},
        "canva_design_type": "magazine",
    },
    "us-letter-2col": {
        "category": "Editorial & Print",
        "name": "US Letter 2-Column Policy Brief / Whitepaper (8.5 x 11 in)",
        "unit": "pt",
        "dimensions": {"width": 612.0, "height": 792.0, "inches": [8.5, 11.0]},
        "bleed_per_side_pt": BLEED_PT,
        "safe_margin_pt": SAFE_MARGIN_PT,
        "live_area": {"width": 540.0, "height": 720.0, "bounds_pdf": [36.0, 36.0, 576.0, 756.0]},
        "grid": {
            "gutter_pt": 18.0,
            "columns": [
                {"index": 1, "role": "narrative_core", "x_start_pt": 36.0, "width_pt": 300.0},
                {"index": 2, "role": "callouts_sidebar", "x_start_pt": 354.0, "width_pt": 222.0},
            ],
        },
        "recommended_typography": {"hero_pt": "28-38", "h2_pt": "15-18", "body_min_pt": 11.0, "leading_pt": "15.0-17.0"},
        "canva_design_type": "report",
    },
    "a4-editorial": {
        "category": "Editorial & Print",
        "name": "A4 International Document / Brochure (210 x 297 mm)",
        "unit": "pt",
        "dimensions": {"width": 595.28, "height": 841.89, "mm": [210, 297]},
        "bleed_per_side_pt": 8.5,
        "safe_margin_pt": 36.0,
        "live_area": {"width": 523.28, "height": 769.89},
        "grid": {"gutter_pt": 18.0, "columns": 2, "column_width_pt": 252.64},
        "recommended_typography": {"hero_pt": "28-40", "h2_pt": "15-18", "body_min_pt": 11.0, "leading_pt": "14.5-16.5"},
        "canva_design_type": "document",
    },
    "poster-18x24": {
        "category": "Print & Signage",
        "name": "Print Poster / Event Flyer (18 x 24 in)",
        "unit": "pt",
        "dimensions": {"width": 1296.0, "height": 1728.0, "inches": [18, 24]},
        "bleed_per_side_pt": 9.0,
        "safe_margin_pt": 54.0,
        "live_area": {"width": 1188.0, "height": 1620.0},
        "canva_design_type": "poster",
    },
    "business-card": {
        "category": "Brand Collateral",
        "name": "Standard US Business Card (3.5 x 2 in)",
        "unit": "pt",
        "dimensions": {"width": 252.0, "height": 144.0, "inches": [3.5, 2.0]},
        "bleed_per_side_pt": 9.0,
        "safe_margin_pt": 14.4,
        "live_area": {"width": 223.2, "height": 115.2},
        "canva_design_type": "business_card",
    },
}


def list_design_presets() -> list[dict[str, Any]]:
    return [
        {
            "preset_id": key,
            "category": val["category"],
            "name": val["name"],
            "unit": val["unit"],
            "dimensions": val["dimensions"],
            "canva_design_type": val.get("canva_design_type", "custom"),
        }
        for key, val in DESIGN_PRESETS.items()
    ]


def compute_layout_spec(preset: str = "us-letter-3col") -> dict[str, Any]:
    """Return exact dimensions, safe margins, grids, typography, and color tokens for any Canva format."""
    if preset not in DESIGN_PRESETS:
        raise KeyError(f"Unknown format preset '{preset}'. Available: {sorted(DESIGN_PRESETS.keys())}")

    return {
        "preset_id": preset,
        "spec": DESIGN_PRESETS[preset],
        "universal_rules": {
            "body_min_pt_print": 11.0,
            "areatext_height_formula": "H >= (total_lines * leading_pt) + 20.0",
            "illustrator_pointtext_top_rule": "tf.top = -bbox[1] (geometric top, never baseline origin_y)",
        },
        "available_presets": sorted(DESIGN_PRESETS.keys()),
    }


def _require_fitz() -> Any:
    try:
        import fitz  # type: ignore

        return fitz
    except ImportError as exc:
        raise RuntimeError(
            "PyMuPDF ('pymupdf') is required for PDF prepress inspection. "
            "Install it with: pip install pymupdf"
        ) from exc


def inspect_pdf(pdf_path: str, max_pages: int = 5, safe_margin_pt: float = SAFE_MARGIN_PT) -> dict[str, Any]:
    """Inspect a Canva-exported PDF for page geometry, embedded fonts, margin compliance, and text blocks."""
    fitz = _require_fitz()
    path = Path(pdf_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")

    doc = fitz.open(str(path))
    pages_out = []
    unique_fonts: dict[str, dict[str, Any]] = {}

    for page_idx in range(min(len(doc), max_pages)):
        page = doc[page_idx]
        rect = page.rect
        fonts = page.get_fonts(full=True)
        for f in fonts:
            xref = f[0]
            basefont = str(f[3]).split("+")[-1]
            unique_fonts[basefont] = {"xref": xref, "name": basefont, "ext": f[1], "type": f[2]}

        text_dict = page.get_text("dict")
        blocks_summary = []
        below_11pt_count = 0
        outside_safe_margin_count = 0

        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            bbox = [round(v, 2) for v in block.get("bbox", [0, 0, 0, 0])]
            lines = block.get("lines", [])
            block_text_parts = []
            sizes = set()
            font_names = set()
            for line in lines:
                for span in line.get("spans", []):
                    t = span.get("text", "")
                    if t.strip():
                        block_text_parts.append(t)
                        sz = round(float(span.get("size", 0)), 2)
                        sizes.add(sz)
                        font_names.add(str(span.get("font", "")).split("+")[-1])
                        if 0 < sz < 10.95:
                            below_11pt_count += 1

            text_joined = " ".join(block_text_parts).strip()
            if not text_joined:
                continue

            if (
                bbox[0] < safe_margin_pt - 1.0
                or bbox[1] < safe_margin_pt - 1.0
                or bbox[2] > rect.width - safe_margin_pt + 1.0
                or bbox[3] > rect.height - safe_margin_pt + 1.0
            ):
                outside_safe_margin_count += 1

            blocks_summary.append(
                {
                    "bbox_pt": bbox,
                    "illustrator_top_pt": round(-bbox[1], 2),
                    "illustrator_left_pt": bbox[0],
                    "fonts": sorted(font_names),
                    "sizes_pt": sorted(sizes),
                    "text_preview": text_joined[:160],
                }
            )

        pages_out.append(
            {
                "page_number": page_idx + 1,
                "width_pt": round(rect.width, 2),
                "height_pt": round(rect.height, 2),
                "is_us_letter": math.isclose(rect.width, LETTER_WIDTH_PT, abs_tol=2.0)
                and math.isclose(rect.height, LETTER_HEIGHT_PT, abs_tol=2.0),
                "spans_below_11pt": below_11pt_count,
                "blocks_outside_safe_margin": outside_safe_margin_count,
                "text_block_count": len(blocks_summary),
                "text_blocks": blocks_summary[:40],
            }
        )

    return {
        "file": str(path),
        "total_pages": len(doc),
        "inspected_pages": len(pages_out),
        "unique_fonts": list(unique_fonts.values()),
        "pages": pages_out,
    }


def extract_pdf_fonts(pdf_path: str, output_dir: str) -> dict[str, Any]:
    """Extract all embedded font streams from a Canva vector PDF for prepress handoff."""
    fitz = _require_fitz()
    path = Path(pdf_path).expanduser().resolve()
    out_dir = Path(output_dir).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {path}")
    out_dir.mkdir(parents=True, exist_ok=True)

    doc = fitz.open(str(path))
    seen_xrefs: set[int] = set()
    extracted: list[dict[str, Any]] = []

    for page in doc:
        for f in page.get_fonts(full=True):
            xref = int(f[0])
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            basefont = str(f[3]).split("+")[-1].replace("/", "_").replace(" ", "_")
            name, ext, _, buffer = doc.extract_font(xref)
            if not buffer or not ext:
                continue
            target = out_dir / f"{basefont}.{ext}"
            target.write_bytes(buffer)
            extracted.append(
                {
                    "xref": xref,
                    "font_name": name or basefont,
                    "extension": ext,
                    "bytes": len(buffer),
                    "path": str(target),
                }
            )

    return {
        "pdf": str(path),
        "output_dir": str(out_dir),
        "extracted_count": len(extracted),
        "fonts": extracted,
    }
