from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any


def _asset_path_from_ref(asset: dict[str, Any], *, workspace: Path) -> Path:
    raw_path = str(asset.get("path") or "").strip()
    if raw_path:
        path = Path(raw_path).expanduser()
        if not path.is_absolute():
            path = workspace / path
        return path
    file_name = str(asset.get("file_name") or asset.get("name") or "").strip()
    return workspace / file_name


def _relative_asset_url(asset_path: Path, *, html_path: Path) -> str:
    try:
        return asset_path.resolve().relative_to(html_path.parent.resolve()).as_posix()
    except Exception:
        try:
            return asset_path.resolve().as_uri()
        except Exception:
            return asset_path.as_posix()


def _html_mentions_asset(html_text: str, asset: dict[str, Any]) -> bool:
    file_name = str(asset.get("file_name") or asset.get("name") or "").strip()
    raw_path = str(asset.get("path") or "").strip()
    checks = [file_name, raw_path, raw_path.replace("\\", "/")]
    return any(check and check in html_text for check in checks)


def _inline_asset_markup(asset_path: Path, *, html_path: Path, title: str) -> str:
    suffix = asset_path.suffix.lower()
    if suffix == ".svg":
        src = html.escape(_relative_asset_url(asset_path, html_path=html_path))
        return f'<img class="historical-auto-asset-image" src="{src}" alt="{html.escape(title)}" />'
    if suffix in {".html", ".htm"}:
        try:
            snippet = asset_path.read_text(encoding="utf-8-sig")
        except Exception:
            snippet = ""
        snippet = re.sub(r"(?is)^.*?<body[^>]*>", "", snippet)
        snippet = re.sub(r"(?is)</body>.*$", "", snippet)
        return f'<div class="historical-auto-asset-fragment">{snippet}</div>'
    src = html.escape(_relative_asset_url(asset_path, html_path=html_path))
    return f'<a class="historical-auto-asset-link" href="{src}">{html.escape(asset_path.name)}</a>'


def ensure_historical_deck_assets_embedded(
    *,
    workspace: Path,
    html_path: Path,
    css_path: Path,
    deck_layout_pack_path: Path,
) -> dict[str, Any]:
    """Inject missing deterministic deck assets into historical-style HTML before PDF render.

    Codex writes the main layout, but the backend owns final artifact completeness:
    if deck_layout_pack references chart/table/collage assets that the generated
    HTML forgot to embed, this helper appends print-friendly pages for them.
    """
    html_text = html_path.read_text(encoding="utf-8-sig")
    deck_layout = json.loads(deck_layout_pack_path.read_text(encoding="utf-8-sig"))
    injected_sections: list[str] = []
    injected_assets: list[str] = []
    for page in list(deck_layout.get("pages") or []):
        if not isinstance(page, dict):
            continue
        assets = [asset for asset in list(page.get("asset_refs") or []) if isinstance(asset, dict)]
        missing_assets = [asset for asset in assets if not _html_mentions_asset(html_text, asset)]
        if not missing_assets:
            continue
        page_title = str(page.get("title") or "Deck visual page").strip()
        template_type = str(page.get("page_template_type") or "asset_page").strip()
        module = str(page.get("module") or "").strip()
        blocks: list[str] = []
        for asset in missing_assets:
            asset_path = _asset_path_from_ref(asset, workspace=workspace)
            if not asset_path.exists():
                continue
            title = str(asset.get("title") or asset_path.stem).strip()
            blocks.append(
                '<figure class="historical-auto-asset-card">'
                f'<figcaption>{html.escape(title)}</figcaption>'
                f'{_inline_asset_markup(asset_path, html_path=html_path, title=title)}'
                "</figure>"
            )
            injected_assets.append(asset_path.name)
        if not blocks:
            continue
        injected_sections.append(
            '<section class="deck-page historical-auto-asset-page '
            f'historical-auto-{html.escape(template_type)}">'
            '<div class="historical-auto-page-rail"></div>'
            f'<p class="historical-auto-kicker">{html.escape(module or template_type)}</p>'
            f'<h2>{html.escape(page_title)}</h2>'
            f'<div class="historical-auto-asset-grid">{"".join(blocks)}</div>'
            "</section>"
        )
    if injected_sections:
        injection = "\n<!-- deterministic historical deck asset injection -->\n" + "\n".join(injected_sections) + "\n"
        if re.search(r"</body\s*>", html_text, flags=re.I):
            html_text = re.sub(r"</body\s*>", injection + "</body>", html_text, count=1, flags=re.I)
        else:
            html_text = html_text + injection
        html_path.write_text(html_text, encoding="utf-8")

    css_text = css_path.read_text(encoding="utf-8-sig")
    if "historical-auto-asset-page" not in css_text:
        css_text += """

/* Deterministic historical deck asset injection */
.historical-auto-asset-page {
  break-after: page;
  page-break-after: always;
  position: relative;
  min-height: 260mm;
  padding: 22mm 18mm 16mm 24mm;
  background: #ffffff;
  color: #17314a;
  overflow: hidden;
}
.historical-auto-page-rail {
  position: absolute;
  left: 10mm;
  top: 22mm;
  width: 4mm;
  height: 42mm;
  background: #1d8bc8;
}
.historical-auto-kicker {
  margin: 0 0 6mm;
  color: #1d8bc8;
  font-size: 9pt;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}
.historical-auto-asset-page h2 {
  margin: 0 0 10mm;
  max-width: 170mm;
  color: #0b4f83;
  font-size: 22pt;
  line-height: 1.18;
}
.historical-auto-asset-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8mm;
}
.historical-auto-asset-card {
  margin: 0;
  padding: 5mm;
  border: 1px solid #d7e7f2;
  border-radius: 4mm;
  background: #f8fbff;
}
.historical-auto-asset-card figcaption {
  margin-bottom: 4mm;
  color: #17314a;
  font-size: 10pt;
  font-weight: 700;
}
.historical-auto-asset-image {
  display: block;
  width: 100%;
  max-height: 112mm;
  object-fit: contain;
}
.historical-auto-asset-fragment {
  overflow: hidden;
}
"""
        css_path.write_text(css_text, encoding="utf-8")
    return {
        "injected_section_count": len(injected_sections),
        "injected_asset_count": len(injected_assets),
        "injected_assets": injected_assets,
    }
