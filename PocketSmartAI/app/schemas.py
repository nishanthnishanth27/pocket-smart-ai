from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field


class RegisterRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=80,
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=128,
    )


class LoginRequest(BaseModel):
    email: EmailStr

    password: str


class HomeRequest(BaseModel):
    budget: float = Field(
        gt=0,
        le=10_000_000,
    )

    room_type: str = Field(
        min_length=2,
        max_length=80,
    )

    style: str = Field(
        default="Modern",
        max_length=80,
    )

    items: str = Field(
        default="lights, ceiling fan, storage",
        max_length=500,
    )

    city: str = Field(
        default="Chennai",
        max_length=80,
    )


class PartyRequest(BaseModel):
    budget: float = Field(
        gt=0,
        le=10_000_000,
    )

    event_type: str = Field(
        min_length=2,
        max_length=80,
    )

    guests: int = Field(
        gt=0,
        le=10_000,
    )

    venue: str = Field(
        default="Indoor",
        max_length=100,
    )

    city: str = Field(
        default="Chennai",
        max_length=80,
    )

    food_preference: str = Field(
        default="Mixed",
        max_length=100,
    )


class RecommendationItem(BaseModel):
    name: str
    category: str
    platform: str

    estimated_price: float = 0

    reason: str

    link: str


class BudgetAllocation(BaseModel):
    category: str

    amount: float

    percentage: float


class RecommendationResponse(BaseModel):
    title: str

    summary: str

    budget: float

    total_estimated: float

    savings: float

    allocations: list[BudgetAllocation] = []

    recommendations: list[RecommendationItem] = []

    tips: list[str] = []

    disclaimer: str


class SessionUser(BaseModel):
    id: int

    name: str

    email: EmailStr

    model_config = ConfigDict(
        from_attributes=True
    )