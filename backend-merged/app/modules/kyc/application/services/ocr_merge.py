"""
Merge split ID front/back OCR dicts into a single id_document shape for KYC entity + risk.
Front wins for portrait-side fields; back wins for MRZ and often expiry.
"""
from typing import Any, Dict, Optional


def _pick_str(f: Dict[str, Any], b: Dict[str, Any], key: str) -> Optional[str]:
    fv, bv = f.get(key), b.get(key)
    if fv is not None and str(fv).strip():
        return str(fv).strip() if not isinstance(fv, str) else fv
    if bv is not None and str(bv).strip():
        return str(bv).strip() if not isinstance(bv, str) else bv
    return None


def merge_id_front_back(id_front: Optional[Dict[str, Any]], id_back: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return merged id_document fields (no confidence keys)."""
    f = {k: v for k, v in dict(id_front or {}).items() if k != "confidence"}
    b = {k: v for k, v in dict(id_back or {}).items() if k != "confidence"}
    merged: Dict[str, Any] = {}
    for key in (
        "full_name",
        "date_of_birth",
        "document_type",
        "document_number",
        "gender",
        "nationality",
        "place_of_birth",
        "issue_date",
    ):
        merged[key] = _pick_str(f, b, key)

    merged["expiry_date"] = _pick_str(f, b, "expiry_date")
    if not merged.get("expiry_date"):
        merged["expiry_date"] = _pick_str(b, f, "expiry_date")

    merged["mrz_line1"] = _pick_str(b, f, "mrz_line1")
    merged["mrz_line2"] = _pick_str(b, f, "mrz_line2")

    return merged


def average_id_confidence(front_conf: float, back_conf: Optional[float], had_back: bool) -> float:
    if had_back and back_conf is not None:
        return (float(front_conf) + float(back_conf)) / 2.0
    return float(front_conf)
