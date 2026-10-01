import os


# Test database
os.environ["DATABASE_URL"] = (
    "sqlite:///./test_pocketsmart.db"
)

os.environ["SECRET_KEY"] = (
    "test-secret-key"
)

# Empty key means fallback engine.
os.environ["GEMINI_API_KEY"] = ""


from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"


def test_register_login_and_home():

    email = "tester@example.com"

    response = client.post(
        "/api/auth/register",

        json={
            "name": "Tester",

            "email": email,

            "password": "secret123",
        },
    )

    # Account can already exist from
    # an earlier test run.
    assert response.status_code in {
        200,
        409,
    }


    if response.status_code == 409:

        response = client.post(
            "/api/auth/login",

            json={
                "email": email,

                "password": "secret123",
            },
        )

        assert response.status_code == 200


    response = client.get(
        "/api/auth/me"
    )

    assert response.status_code == 200


    response = client.post(
        "/api/planners/home",

        json={
            "budget": 30000,

            "room_type": "Living Room",

            "style": "Modern",

            "items": "sofa, lights",

            "city": "Chennai",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["planner"] == "home"

    assert (
        data["result"]["budget"]
        == 30000
    )


def test_party_planner():

    email = "partytester@example.com"

    client.post(
        "/api/auth/register",

        json={
            "name": "Party Tester",

            "email": email,

            "password": "secret123",
        },
    )


    client.post(
        "/api/auth/login",

        json={
            "email": email,

            "password": "secret123",
        },
    )


    response = client.post(
        "/api/planners/party",

        json={
            "budget": 40000,

            "event_type": "Birthday",

            "guests": 50,

            "venue": "Indoor",

            "city": "Chennai",

            "food_preference": "Mixed",
        },
    )


    assert response.status_code == 200

    data = response.json()

    assert data["planner"] == "party"


def test_history():

    response = client.get(
        "/api/history"
    )

    assert response.status_code == 200

    assert isinstance(
        response.json(),
        list,
    )