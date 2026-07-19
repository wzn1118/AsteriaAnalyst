from __future__ import annotations

from app.services.report_service import _procurement_management_release_allowed


def test_procurement_management_release_requires_independent_validator() -> None:
    assert _procurement_management_release_allowed(
        {"passed": True},
        {"score": 95},
        {"passed": False},
    ) is False


def test_procurement_management_release_allows_only_complete_passes() -> None:
    assert _procurement_management_release_allowed(
        {"passed": True},
        {"score": 90},
        {"passed": True},
    ) is True
    assert _procurement_management_release_allowed(
        {"passed": True},
        {"score": "not-a-score"},
        {"passed": True},
    ) is False
