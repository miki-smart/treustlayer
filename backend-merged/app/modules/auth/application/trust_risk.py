"""Map trust_score to risk_level and risk_flag for JWT / introspection claims."""


def risk_level_and_flag(trust_score: float | None) -> tuple[str, bool]:
    """
    Align with relying-party expectations: risk_flag True when trust_score < 30.
    """
    if trust_score is None:
        return "high", True
    s = float(trust_score)
    if s < 30:
        return "high", True
    if s < 60:
        return "medium", False
    return "low", False
