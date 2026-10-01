from app.ai.gemini_service import _normalize_response


def _model_response(price=35):
    return {
        "title": "Plan",
        "summary": "A practical plan.",
        "budget": 999,
        "total_estimated": 999,
        "savings": -1,
        "allocations": [
            {"category": "Main", "amount": 1000, "percentage": 75},
            {"category": "Buffer", "amount": 0, "percentage": 25},
        ],
        "recommendations": [
            {
                "name": "Useful item",
                "category": "Home",
                "platform": "untrusted platform",
                "estimated_price": price,
                "reason": "Fits the requested plan.",
                "link": "https://example.invalid/product",
            }
        ],
        "tips": ["Compare final costs before ordering."],
        "disclaimer": "Estimate only.",
    }


def test_model_response_is_normalized_to_user_budget():
    result = _normalize_response(_model_response(), "home", {"budget": 100})

    assert result is not None
    assert result["budget"] == 100
    assert result["total_estimated"] == 35
    assert result["savings"] == 65
    assert sum(item["amount"] for item in result["allocations"]) == 100
    assert result["recommendations"][0]["platform"] == "Amazon"
    assert result["recommendations"][0]["link"].startswith("https://www.amazon.in/")


def test_model_response_over_budget_is_rejected():
    assert _normalize_response(_model_response(price=101), "home", {"budget": 100}) is None
