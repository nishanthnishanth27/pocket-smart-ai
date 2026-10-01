import json
from typing import Optional

from google import genai
from google.genai import types

from .catalog import fallback_home
from .catalog import fallback_party
from .catalog import fallback_jewelry

from .config import get_settings


settings = get_settings()


def _client():
    """
    Create Gemini client only when an API key exists.
    """

    if not settings.gemini_api_key:
        return None

    return genai.Client(
        api_key=settings.gemini_api_key
    )


def _response_schema():
    """
    Structured JSON schema returned by Gemini.
    """

    return {
        "type": "object",

        "properties": {

            "title": {
                "type": "string"
            },

            "summary": {
                "type": "string"
            },

            "budget": {
                "type": "number"
            },

            "total_estimated": {
                "type": "number"
            },

            "savings": {
                "type": "number"
            },

            "allocations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {

                        "category": {
                            "type": "string"
                        },

                        "amount": {
                            "type": "number"
                        },

                        "percentage": {
                            "type": "number"
                        },
                    },

                    "required": [
                        "category",
                        "amount",
                        "percentage",
                    ],
                },
            },

            "recommendations": {
                "type": "array",

                "items": {
                    "type": "object",

                    "properties": {

                        "name": {
                            "type": "string"
                        },

                        "category": {
                            "type": "string"
                        },

                        "platform": {
                            "type": "string"
                        },

                        "estimated_price": {
                            "type": "number"
                        },

                        "reason": {
                            "type": "string"
                        },

                        "link": {
                            "type": "string"
                        },
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

            "tips": {
                "type": "array",

                "items": {
                    "type": "string"
                },
            },

            "disclaimer": {
                "type": "string"
            },
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


def _create_prompt(
    planner_type: str,
    data: dict,
) -> str:

    return f"""
You are PocketSmart AI.

You are a budget-aware recommendation assistant.

Planner:
{planner_type}

User information:
{json.dumps(data, ensure_ascii=False)}

Your task is to create useful, practical recommendations.

Rules:

1. Use Indian Rupees.
2. Respect the user's budget.
3. Keep estimated total spending at or below the budget whenever reasonable.
4. Give 4 to 8 recommendations.
5. Provide budget allocations.
6. Give practical tips.
7. Use these platforms where relevant:

Amazon
Flipkart
IKEA
Swiggy
Zomato
OYO

8. Links can be search links.
9. Never invent a specific product URL.
10. Never claim that a price is live.
11. Never claim guaranteed stock.
12. Clearly state that prices are estimates.
13. For jewelry image analysis, only use the image for broad color/style observations.
14. Do not identify the person in the image.
15. Return ONLY JSON matching the requested schema.
"""


def _generate(
    planner_type: str,
    data: dict,
    image_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
):

    if planner_type == "home":

        fallback = fallback_home(data)

    elif planner_type == "party":

        fallback = fallback_party(data)

    else:

        fallback = fallback_jewelry(
            data,
            bool(image_bytes),
        )

    client = _client()

    # No API key.
    if client is None:
        return fallback

    try:

        contents = [
            _create_prompt(
                planner_type,
                data,
            )
        ]

        if image_bytes and mime_type:

            image_part = types.Part.from_bytes(
                data=image_bytes,
                mime_type=mime_type,
            )

            contents.insert(
                0,
                image_part,
            )

        response = client.models.generate_content(

            model=settings.gemini_model,

            contents=contents,

            config=types.GenerateContentConfig(

                response_mime_type="application/json",

                response_schema=_response_schema(),

                temperature=0.35,
            ),
        )

        parsed = json.loads(
            response.text
        )

        # Always trust the submitted budget.
        parsed["budget"] = float(
            data["budget"]
        )

        return parsed

    except Exception:
        # Keep application usable if
        # Gemini fails.
        return fallback


def generate_home(data: dict):
    return _generate(
        "home",
        data,
    )


def generate_party(data: dict):
    return _generate(
        "party",
        data,
    )


def generate_jewelry(
    data: dict,
    image_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
):

    return _generate(
        "jewelry",
        data,
        image_bytes,
        mime_type,
    )