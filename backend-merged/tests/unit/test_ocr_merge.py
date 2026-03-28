"""Tests for ID front/back merge helper."""
from app.modules.kyc.application.services.ocr_merge import (
    average_id_confidence,
    merge_id_front_back,
)


def test_merge_prefers_front_for_name_back_for_mrz():
    f = {"full_name": "A B", "document_number": "F1", "mrz_line1": "bad"}
    b = {"mrz_line1": "GOODMRZ", "mrz_line2": "LINE2", "expiry_date": "2030-01-01"}
    m = merge_id_front_back(f, b)
    assert m["full_name"] == "A B"
    assert m["document_number"] == "F1"
    assert m["mrz_line1"] == "GOODMRZ"
    assert m["mrz_line2"] == "LINE2"
    assert m["expiry_date"] == "2030-01-01"


def test_average_id_confidence():
    assert average_id_confidence(0.8, 0.6, True) == 0.7
    assert average_id_confidence(0.9, None, False) == 0.9
