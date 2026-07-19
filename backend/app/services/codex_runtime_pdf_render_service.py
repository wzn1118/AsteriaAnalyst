from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
from typing import Any


EDGE_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
]


def _resolve_edge_executable() -> Path:
    configured = os.getenv("ASTERIA_EDGE_EXECUTABLE") or os.getenv("EDGE_EXECUTABLE")
    if configured:
        candidate = Path(configured).expanduser().resolve()
        if candidate.exists() and candidate.is_file():
            return candidate
        raise FileNotFoundError(f"Configured Edge executable not found: {candidate}")
    discovered = shutil.which("msedge") or shutil.which("msedge.exe")
    if discovered:
        return Path(discovered).resolve()
    for candidate in EDGE_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError("Microsoft Edge executable not found in expected locations.")


def _validate_html_css_inputs(html_path: Path, css_path: Path) -> None:
    if not html_path.exists():
        raise FileNotFoundError(f"HTML input not found: {html_path}")
    if not css_path.exists():
        raise FileNotFoundError(f"CSS input not found: {css_path}")

    html_text = html_path.read_text(encoding="utf-8")
    expected_css_name = css_path.name
    if expected_css_name not in html_text:
        raise ValueError(
            f"HTML input does not reference {expected_css_name} with the expected relative path."
        )


def render_html_to_pdf(
    *,
    html_path: Path,
    css_path: Path,
    output_pdf_path: Path,
    timeout_sec: int = 120,
) -> dict[str, Any]:
    """
    Deterministically render a local HTML/CSS report package to PDF using
    Microsoft Edge headless mode.

    This helper intentionally performs no LLM work.
    """

    _validate_html_css_inputs(html_path, css_path)
    edge_executable = _resolve_edge_executable()

    output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
    temp_output_pdf_path = output_pdf_path.with_name(f"{output_pdf_path.stem}.tmp{output_pdf_path.suffix}")
    if temp_output_pdf_path.exists():
        temp_output_pdf_path.unlink()

    attempts = [
        {"headless_flag": "--headless=new", "label": "edge_headless_new"},
        {"headless_flag": "--headless", "label": "edge_headless_legacy"},
    ]
    proc: subprocess.CompletedProcess[str] | None = None
    selected_engine = "edge_headless"
    failure_details: list[str] = []

    for attempt_index, attempt in enumerate(attempts, start=1):
        temp_output_pdf_path.unlink(missing_ok=True)
        profile_dir = Path(tempfile.mkdtemp(prefix="codex-edge-pdf-"))
        cache_dir = profile_dir / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        args = [
            str(edge_executable),
            str(attempt["headless_flag"]),
            "--disable-gpu",
            "--disable-extensions",
            "--disable-crash-reporter",
            "--disable-crashpad",
            "--disable-features=Crashpad",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={profile_dir}",
            f"--disk-cache-dir={cache_dir}",
            "--print-to-pdf-no-header",
            "--no-pdf-header-footer",
            f"--print-to-pdf={temp_output_pdf_path}",
            html_path.resolve().as_uri(),
        ]
        try:
            try:
                proc = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout_sec,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                failure_details.append(
                    f"attempt_{attempt_index}:{attempt['label']}:timeout_after_{timeout_sec}s"
                )
                temp_output_pdf_path.unlink(missing_ok=True)
                proc = None
                if attempt_index < len(attempts):
                    time.sleep(1.0)
                    continue
                raise RuntimeError(
                    "PDF render did not produce output file: "
                    + " | ".join(failure_details)
                ) from exc
        finally:
            shutil.rmtree(profile_dir, ignore_errors=True)

        if temp_output_pdf_path.exists():
            selected_engine = str(attempt["label"])
            break

        stderr_excerpt = (proc.stderr or "").strip() if proc else ""
        stdout_excerpt = (proc.stdout or "").strip() if proc else ""
        detail = stderr_excerpt or stdout_excerpt or f"Edge exited with code {proc.returncode if proc else 'unknown'}"
        failure_details.append(f"attempt_{attempt_index}:{attempt['label']}:{detail}")
        if attempt_index < len(attempts):
            time.sleep(1.0)

    if not temp_output_pdf_path.exists():
        raise RuntimeError(f"PDF render did not produce output file: {' | '.join(failure_details)}")

    file_size = temp_output_pdf_path.stat().st_size
    if file_size <= 0:
        temp_output_pdf_path.unlink(missing_ok=True)
        raise RuntimeError("PDF render produced an empty file.")

    temp_output_pdf_path.replace(output_pdf_path)

    return {
        "engine": selected_engine,
        "executable_path": str(edge_executable.resolve()),
        "html_path": str(html_path.resolve()),
        "css_path": str(css_path.resolve()),
        "pdf_path": str(output_pdf_path.resolve()),
        "bytes": file_size,
        "return_code": proc.returncode if proc else None,
        "stdout": proc.stdout if proc else "",
        "stderr": proc.stderr if proc else "",
        "attempt_failures": failure_details,
    }
