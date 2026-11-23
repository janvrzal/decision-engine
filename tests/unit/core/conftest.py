"""Společná data pro testy jádra."""

from typing import Any

import pytest


def valid_project_data() -> dict[str, Any]:
    """Platná zakázka 1D ve tvaru JSON (jako z importu nebo API)."""
    return {
        "id": "zakazka-1",
        "name": "Regál do dílny",
        "format_version": 1,
        "task_type": "cutting_1d",
        "revision": 0,
        "problem": {
            "material": "jekl 40×40×2",
            "parts": [
                {"id": "p1", "name": "noha", "length_mm": 1800, "quantity": 4},
                {"id": "p2", "name": "polička", "length_mm": 1200, "quantity": 8},
            ],
            "stock": [{"id": "s1", "length_mm": 6000, "price": "320.00"}],
        },
        "parameters": {
            "kerf_mm": 3,
            "trim_mm": 0,
            "min_remnant_mm": 300,
            "objective": "cheapest",
            "time_limit_s": 10,
        },
    }


@pytest.fixture
def project_data() -> dict[str, Any]:
    return valid_project_data()
