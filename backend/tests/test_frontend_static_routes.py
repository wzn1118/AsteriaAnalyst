from __future__ import annotations

from fastapi.testclient import TestClient

import app.main as main_module


def _write_export_file(frontend_dir, relative_path: str, body: str) -> None:
    target = frontend_dir / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")


def test_static_export_entry_routes_include_home_and_method_guide(tmp_path, monkeypatch) -> None:
    _write_export_file(tmp_path, "index.html", "<h1>Asteria home</h1>")
    _write_export_file(tmp_path, "analysis.html", "<h1>Analysis</h1>")
    _write_export_file(tmp_path, "lab.html", "<h1>Lab</h1>")
    _write_export_file(tmp_path, "lab/method-guide.html", "<h1>Method guide</h1>")
    _write_export_file(tmp_path, "revision.html", "<h1>Revision</h1>")
    _write_export_file(tmp_path, "revision/workspace.html", "<h1>Revision workspace</h1>")
    monkeypatch.setattr(main_module, "frontend_dist_dir", lambda: tmp_path)

    client = TestClient(main_module.app)
    expected = {
        "/": "Asteria home",
        "/analysis": "Analysis",
        "/lab": "Lab",
        "/lab/method-guide": "Method guide",
        "/revision": "Revision",
        "/revision/workspace": "Revision workspace",
    }

    for path, body in expected.items():
        response = client.get(path)
        assert response.status_code == 200
        assert body in response.text

        head_response = client.head(path)
        assert head_response.status_code == 200
