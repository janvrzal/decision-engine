"""Testy typů Ok a Err (ADR-0001: chyby jako hodnoty)."""

import dataclasses

import pytest

from decision_engine.core.result import Err, Ok, Result


def _divide(a: int, b: int) -> Result[int, str]:
    if b == 0:
        return Err("dělení nulou")
    return Ok(a // b)


def test_ok_nese_hodnotu() -> None:
    assert _divide(6, 3) == Ok(2)


def test_err_nese_chybu() -> None:
    assert _divide(1, 0) == Err("dělení nulou")


def test_vysledek_jde_rozlisit_matchem() -> None:
    match _divide(1, 0):
        case Ok(value):
            pytest.fail(f"čekal jsem chybu, přišlo {value}")
        case Err(error):
            assert error == "dělení nulou"


def test_ok_a_err_se_stejnym_obsahem_nejsou_shodne() -> None:
    assert Ok(1) != Err(1)


@pytest.mark.parametrize(("result", "field"), [(Ok(1), "value"), (Err("x"), "error")])
def test_vysledek_je_nemenny(result: Result[int, str], field: str) -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(result, field, 2)
