from davy_event.ai_extraction import extract_with_model


def test_model_extraction_requires_verbatim_evidence():
    source = "周末亲子市集将于2026年11月15日举行，地点在滨海湾。"

    def model(prompt, text):
        assert "Return ONLY valid JSON" in prompt
        return {
            "events": [{
                "title": "周末亲子市集",
                "start_datetime": "2026-11-15",
                "city": "Singapore",
                "evidence": [{"quote": "周末亲子市集将于2026年11月15日举行"}],
            }]
        }

    events = extract_with_model(
        source, model, source_url="https://events.test/market", source_platform="xhs"
    )
    assert len(events) == 1
    assert events[0]["title"] == "周末亲子市集"
    assert events[0]["verification_status"] == "source_claim"
    assert events[0]["evidence"][0]["quote"] in source


def test_model_extraction_rejects_unverifiable_model_claims():
    def model(prompt, text):
        return {"events": [{
            "title": "Invented event",
            "start_datetime": "2026-11-15",
            "evidence": [{"quote": "This quote does not exist"}],
        }]}

    assert extract_with_model("Actual source text", model) == []


def test_model_extraction_rejects_non_json_string():
    def model(prompt, text):
        return "Here are some events."

    try:
        extract_with_model("source", model)
    except ValueError as exc:
        assert "valid JSON" in str(exc)
    else:
        raise AssertionError("Expected invalid model output to be rejected")
