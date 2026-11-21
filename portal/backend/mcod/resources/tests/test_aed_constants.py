import pytest

from mcod.resources.aed_aggregation import normalize_header
from mcod.resources.aed_constants import (
    AED_ALLOWED_LICENSES,
    AED_HEADER_ALIASES,
    AED_MINIMUM_COLUMNS,
    AED_TEMPLATE_COLUMNS,
    MAIN_AED_COLUMNS,
)


@pytest.mark.feat_main_aed
def test_template_columns_count_and_unique():
    assert len(AED_TEMPLATE_COLUMNS) == 41
    assert len(set(AED_TEMPLATE_COLUMNS)) == 41
    assert AED_TEMPLATE_COLUMNS[0] == "id_zrodlowe"
    assert AED_TEMPLATE_COLUMNS[-1] == "data_aktualizacji"


@pytest.mark.feat_main_aed
def test_main_columns_count_order():
    assert len(MAIN_AED_COLUMNS) == 51
    assert len(set(MAIN_AED_COLUMNS)) == 51
    assert MAIN_AED_COLUMNS[0] == "id_aed"
    assert MAIN_AED_COLUMNS[-1] == "data_agregacji"
    assert MAIN_AED_COLUMNS[1:42] == AED_TEMPLATE_COLUMNS


@pytest.mark.feat_main_aed
def test_minimum_subset_of_template():
    assert set(AED_MINIMUM_COLUMNS) <= set(AED_TEMPLATE_COLUMNS)


@pytest.mark.feat_main_aed
def test_aliases_target_template_columns():
    assert set(AED_HEADER_ALIASES.values()) <= set(AED_TEMPLATE_COLUMNS)


@pytest.mark.feat_main_aed
def test_alias_keys_are_normalized():
    for key in AED_HEADER_ALIASES:
        assert normalize_header(key) == key


@pytest.mark.feat_main_aed
def test_alias_keys_do_not_shadow_template():
    assert not set(AED_HEADER_ALIASES) & set(AED_TEMPLATE_COLUMNS)


@pytest.mark.feat_main_aed
def test_ambiguous_headers_have_no_alias():
    for ambiguous in ("lokalizacja", "adres", "description"):
        assert ambiguous not in AED_HEADER_ALIASES


@pytest.mark.feat_main_aed
def test_allowed_licenses_exclude_share_alike():
    assert AED_ALLOWED_LICENSES == ("CC0 1.0", "CC BY 4.0")
