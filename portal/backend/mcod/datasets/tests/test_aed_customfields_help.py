import pytest

from mcod.datasets.forms import DatasetForm
from mcod.lib.widgets import JsonPairDatasetInputs
from mcod.resources.aed_constants import AED_MINIMUM_COLUMNS


@pytest.mark.feat_main_aed
def test_customfields_help_text_mentions_aed():
    help_text = DatasetForm.base_fields["customfields"].help_text

    assert "<b>standard</b>" in help_text
    assert "<b>AED</b>" in help_text
    assert all(column in help_text for column in AED_MINIMUM_COLUMNS)


@pytest.mark.feat_main_aed
def test_customfields_field_unchanged():
    field = DatasetForm.base_fields["customfields"]

    assert field.required is False
    assert isinstance(field.widget, JsonPairDatasetInputs)
