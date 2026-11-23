"""Kontrola, že balíček a jeho vrstvy jsou importovatelné."""

import importlib

import pytest


@pytest.mark.parametrize(
    "modul",
    [
        "decision_engine",
        "decision_engine.core",
        "decision_engine.capabilities",
        "decision_engine.adapters",
        "decision_engine.ui",
    ],
)
def test_vrstva_je_importovatelna(modul: str) -> None:
    importlib.import_module(modul)
