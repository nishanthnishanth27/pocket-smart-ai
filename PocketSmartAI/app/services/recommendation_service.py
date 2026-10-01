import json
from typing import Optional

from sqlalchemy.orm import Session

from ..ai.gemini_service import generate_home, generate_jewelry, generate_party
from ..models import RecommendationHistory, User

_GENERATORS = {
    "home": generate_home,
    "party": generate_party,
}


def generate_recommendation(
    kind: str,
    data: dict,
    image_bytes: Optional[bytes] = None,
    mime_type: Optional[str] = None,
) -> dict:
    if kind == "jewelry":
        return generate_jewelry(data, image_bytes, mime_type)
    try:
        generator = _GENERATORS[kind]
    except KeyError as error:
        raise ValueError(f"Unsupported planner: {kind}") from error
    return generator(data)


def save_recommendation(
    db: Session, user: User, kind: str, request_data: dict, result: dict
) -> int:
    row = RecommendationHistory(
        user_id=user.id,
        planner_type=kind,
        request_json=json.dumps(request_data, ensure_ascii=False),
        result_json=json.dumps(result, ensure_ascii=False),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row.id
