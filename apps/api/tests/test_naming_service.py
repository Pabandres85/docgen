import pytest

from app.services.naming import apply_pattern, extract_pattern_fields, safe_filename


def test_safe_filename_removes_invalid_chars():
    assert safe_filename("A/B:C*D?E<F>G|H") == "A_B_C_D_E_F_G_H"


def test_apply_pattern_uses_row_index():
    row = {"NumeroProceso": "123"}
    result = apply_pattern("Proceso_{NumeroProceso}_{row_index}", row, 4)
    assert result == "Proceso_123_4"


def test_apply_pattern_fails_for_missing_column():
    with pytest.raises(KeyError):
        apply_pattern("Proceso_{NoExiste}", {"NumeroProceso": "1"}, 1)


def test_extract_pattern_fields_ignores_literals():
    fields = extract_pattern_fields("Proceso_{NumeroProceso}_{NombreContribuyente}_{row_index}")
    assert fields == {"NumeroProceso", "NombreContribuyente", "row_index"}
