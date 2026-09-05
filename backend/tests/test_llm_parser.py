from datetime import date
from app.services.llm_service import llm_service


def test_hinglish_definite_date_parsing():
    base_date = date(2026, 9, 1)  # Tuesday

    # Test "kal" -> 2026-09-02
    res_kal = llm_service.parse_hinglish_commitment(
        message="Kal subah pakka pay kar dunga",
        current_date=base_date,
        amount=499.0,
    )
    assert res_kal.has_commitment is True
    assert res_kal.promised_date == date(2026, 9, 2)
    assert res_kal.is_ambiguous is False

    # Test "5 tareekh" -> 2026-09-05
    res_date = llm_service.parse_hinglish_commitment(
        message="Bhai 5 tareekh ko done",
        current_date=base_date,
        amount=999.0,
    )
    assert res_date.has_commitment is True
    assert res_date.promised_date == date(2026, 9, 5)

    # Test "somvar" -> Next Monday (2026-09-07)
    res_somvar = llm_service.parse_hinglish_commitment(
        message="Agle somvar salary aane par dunga",
        current_date=base_date,
        amount=1499.0,
    )
    assert res_somvar.has_commitment is True
    assert res_somvar.promised_date == date(2026, 9, 7)


def test_hinglish_ambiguity_detection():
    base_date = date(2026, 9, 1)

    # Ambiguous reply
    res = llm_service.parse_hinglish_commitment(
        message="Jaldi hi de dunga thoda time do",
        current_date=base_date,
        amount=500.0,
    )
    assert res.has_commitment is False
    assert res.is_ambiguous is True
    assert res.clarification_message is not None
    assert "anumaanit tareekh" in res.clarification_message


def test_refusal_detection():
    base_date = date(2026, 9, 1)

    res = llm_service.parse_hinglish_commitment(
        message="Nahi dunga, subscription cancel karo mera",
        current_date=base_date,
        amount=500.0,
    )
    assert res.refused is True
    assert res.has_commitment is False
