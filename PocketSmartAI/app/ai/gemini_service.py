import json
import math
from typing import Optional

from google import genai
from google.genai import types

from ..config import get_settings
from ..services.catalog import fallback_home, fallback_jewelry, fallback_party
from ..services.platform_links import PLATFORM_SEARCH, platform_link

settings = get_settings()


def _client():
    if not settings.gemini_api_key:
        return None
    return genai.Client(api_key=settings.gemini_api_key)


def _schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "summary": {"type": "string"},
            "budget": {"type": "number"},
            "total_estimated": {"type": "number"},
            "savings": {"type": "number"},
            "allocations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "category": {"type": "string"},
                        "amount": {"type": "number"},
                        "percentage": {"type": "number"},
                    },
                    "required": ["category", "amount", "percentage"],
                },
            },
            "recommendations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "category": {"type": "string"},
                        "platform": {"type": "string"},
                        "estimated_price": {"type": "number"},
                        "reason": {"type": "string"},
                        "link": {"type": "string"},
                    },
                    "required": [
                        "name",
                        "category",
                        "platform",
                        "estimated_price",
                        "reason",
                        "link",
                    ],
                },
            },
            "tips": {"type": "array", "items": {"type": "string"}},
            "disclaimer": {"type": "string"},
        },
        "required": [
            "title",
            "summary",
            "budget",
            "total_estimated",
            "savings",
            "allocations",
            "recommendations",
            "tips",
            "disclaimer",
        ],
    }


def _prompt(kind: str, data: dict) -> str:
    planner_guidance = {
        "home": "Prioritize useful room essentials and account for the requested items, room type, style, and city.",
        "party": "Scale catering, venue, and activity recommendations to the guest count, event, venue, and food preference.",
        "jewelry": "Coordinate pieces with the occasion and requested style; use any attached image only for broad outfit colors and style.",
    }[kind]
    return (
        "You are PocketSmart AI, an Indian budget-planning and lifestyle recommendation assistant. "
        f"Create a practical {kind} plan. {planner_guidance} "
        f"User inputs: {json.dumps(data, ensure_ascii=False)}. "
        "Return only JSON matching the response schema. Use INR. Recommend 4 to 8 distinct options, "
        "with plausible approximate costs and clear reasons tied to the user's inputs. Keep estimated "
        "spending within the stated budget; leave money unspent when that is more sensible. Ensure "
        "allocation percentages total 100. Use only these platforms where relevant: "
        f"{', '.join(PLATFORM_SEARCH)}. Provide search-link placeholders only; do not claim live prices, "
        "stock, vendor availability, or product-specific URLs. Include practical tips and a clear disclaimer. "
        "Never infer sensitive personal attributes from an image or identify a person."
    )


def _finite_number(value, default: float = -1) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


def _normalize_response(parsed: dict, kind: str, data: dict) -> Optional[dict]:
    if not isinstance(parsed, dict):
        return None

    budget = _finite_number(data.get("budget"))
    if budget <= 0:
        return None

    raw_recommendations = parsed.get("recommendations")
    if not isinstance(raw_recommendations, list):
        return None

    recommendations = []
    for item in raw_recommendations[:8]:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).strip()[:120]
        category = str(item.get("category", "")).strip()[:80]
        reason = str(item.get("reason", "")).strip()[:500]
        price = _finite_number(item.get("estimated_price"))
        if not name or not category or not reason or price < 0:
            continue
        platform = item.get("platform")
        if platform not in PLATFORM_SEARCH:
            platform = "Amazon"
        recommendations.append(
            {
                "name": name,
                "category": category,
                "platform": platform,
                "estimated_price": round(price, 2),
                "reason": reason,
                "link": platform_link(platform, name),
            }
        )

    if not recommendations:
        return None
    total = round(sum(item["estimated_price"] for item in recommendations), 2)
    if total > budget:
        return None

    raw_allocations = parsed.get("allocations")
    if not isinstance(raw_allocations, list) or not raw_allocations:
        return None
    allocations = []
    for item in raw_allocations[:10]:
        if not isinstance(item, dict):
            continue
        category = str(item.get("category", "")).strip()[:80]
        weight = _finite_number(item.get("percentage"), 0)
        if weight <= 0:
            weight = _finite_number(item.get("amount"), 0)
        if category and weight > 0:
            allocations.append({"category": category, "weight": weight})
    weight_total = sum(item["weight"] for item in allocations)
    if not allocations or not math.isfinite(weight_total) or weight_total <= 0:
        return None

    normalized_allocations = []
    assigned = 0.0
    for index, allocation in enumerate(allocations):
        is_last = index == len(allocations) - 1
        percentage = (
            round(100 - sum(item["percentage"] for item in normalized_allocations), 2)
            if is_last
            else round(allocation["weight"] / weight_total * 100, 2)
        )
        amount = round(budget - assigned, 2) if is_last else round(budget * percentage / 100, 2)
        assigned += amount
        normalized_allocations.append(
            {"category": allocation["category"], "amount": amount, "percentage": percentage}
        )

    tips = parsed.get("tips")
    if not isinstance(tips, list):
        return None
    tips = [str(tip).strip()[:300] for tip in tips if str(tip).strip()][:6]
    if not tips:
        return None

    return {
        "title": str(parsed.get("title", f"{kind.title()} plan")).strip()[:120] or f"{kind.title()} plan",
        "summary": str(parsed.get("summary", "")).strip()[:600],
        "budget": budget,
        "total_estimated": total,
        "savings": round(budget - total, 2),
        "allocations": normalized_allocations,
        "recommendations": recommendations,
        "tips": tips,
        "disclaimer": str(parsed.get("disclaimer", "")).strip()[:500]
        or "Prices and availability are estimates; confirm details with the provider.",
    }


def _fallback(kind: str, data: dict, image_provided: bool) -> dict:
    if kind == "home":
        return fallback_home(data)
    if kind == "party":
        return fallback_party(data)
    return fallback_jewelry(data, image_provided)


def _generate(
    kind: str,
    data: dict,
    image_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
) -> dict:
    fallback = _fallback(kind, data, bool(image_bytes))
    client = _client()
    if not client:
        return fallback

    try:
        contents = [_prompt(kind, data)]
        if image_bytes and mime_type:
            contents.insert(0, types.Part.from_bytes(data=image_bytes, mime_type=mime_type))
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=_schema(),
                temperature=0.35,
            ),
        )
        parsed = json.loads(response.text or "")
        normalized = _normalize_response(parsed, kind, data)
        return normalized if normalized else fallback
    except Exception:
        return fallback


def generate_home(data: dict) -> dict:
    return _generate("home", data)


def generate_party(data: dict) -> dict:
    return _generate("party", data)


def generate_jewelry(
    data: dict, image_bytes: Optional[bytes] = None, mime_type: Optional[str] = None
) -> dict:
    return _generate("jewelry", data, image_bytes, mime_type)
