from urllib.parse import quote_plus


PLATFORM_SEARCH = {
    "Amazon": "https://www.amazon.in/s?k={q}",
    "Flipkart": "https://www.flipkart.com/search?q={q}",
    "IKEA": "https://www.ikea.com/in/en/search/?q={q}",
    "Swiggy": "https://www.swiggy.com/search?query={q}",
    "Zomato": "https://www.zomato.com/search?q={q}",
    "OYO": "https://www.oyorooms.com/search?location={q}",
}


def platform_link(
    platform: str,
    query: str,
) -> str:

    template = PLATFORM_SEARCH.get(
        platform,
        PLATFORM_SEARCH["Amazon"],
    )

    return template.format(
        q=quote_plus(query)
    )


def fallback_home(data: dict) -> dict:

    budget = float(data["budget"])

    items = [
        (
            "LED Ceiling Light",
            "Lighting",
            "Flipkart",
            min(budget * 0.10, 2499),
        ),
        (
            "Compact Storage Cabinet",
            "Storage",
            "IKEA",
            min(budget * 0.28, 8999),
        ),
        (
            "Modern Accent Table",
            "Furniture",
            "Amazon",
            min(budget * 0.22, 6999),
        ),
        (
            "Ceiling Fan",
            "Utility",
            "Amazon",
            min(budget * 0.14, 3999),
        ),
    ]

    recommendations = []

    for (
        name,
        category,
        platform,
        price,
    ) in items:

        recommendations.append(
            {
                "name": name,
                "category": category,
                "platform": platform,
                "estimated_price": round(
                    price,
                    2,
                ),
                "reason": (
                    f"Budget-conscious "
                    f"{data['style']} option for "
                    f"a {data['room_type']}."
                ),
                "link": platform_link(
                    platform,
                    name,
                ),
            }
        )

    total = round(
        sum(
            item["estimated_price"]
            for item in recommendations
        ),
        2,
    )

    return {
        "title": "Home Budget Plan",

        "summary": (
            f"A {data['style']} "
            f"{data['room_type']} plan "
            "focused on useful essentials."
        ),

        "budget": budget,

        "total_estimated": total,

        "savings": max(
            0,
            round(
                budget - total,
                2,
            ),
        ),

        "allocations": [
            {
                "category": "Furniture",
                "amount": round(
                    budget * 0.45,
                    2,
                ),
                "percentage": 45,
            },
            {
                "category": "Lighting",
                "amount": round(
                    budget * 0.20,
                    2,
                ),
                "percentage": 20,
            },
            {
                "category": "Storage",
                "amount": round(
                    budget * 0.25,
                    2,
                ),
                "percentage": 25,
            },
            {
                "category": "Buffer",
                "amount": round(
                    budget * 0.10,
                    2,
                ),
                "percentage": 10,
            },
        ],

        "recommendations": recommendations,

        "tips": [
            "Measure the room before ordering furniture.",
            "Keep 10% of the budget for installation or delivery.",
            "Compare dimensions and warranty before buying.",
        ],

        "disclaimer": (
            "Prices are estimates/search links, "
            "not live inventory or guaranteed quotes."
        ),
    }


def fallback_party(data: dict) -> dict:

    budget = float(data["budget"])

    allocations = [
        ("Catering", 0.50),
        ("Decoration", 0.20),
        ("Entertainment", 0.15),
        ("Venue/Stay", 0.10),
        ("Buffer", 0.05),
    ]

    recommendations_data = [
        (
            "Catering Packages",
            "Catering",
            "Swiggy",
            budget * 0.50,
        ),
        (
            "Event Food Options",
            "Food",
            "Zomato",
            budget * 0.15,
        ),
        (
            "Party Decoration",
            "Decoration",
            "Amazon",
            budget * 0.20,
        ),
        (
            "Guest Accommodation",
            "Accommodation",
            "OYO",
            budget * 0.10,
        ),
    ]

    recommendations = []

    for (
        name,
        category,
        platform,
        price,
    ) in recommendations_data:

        recommendations.append(
            {
                "name": name,
                "category": category,
                "platform": platform,
                "estimated_price": round(
                    price,
                    2,
                ),
                "reason": (
                    f"Suitable starting point "
                    f"for {data['event_type']} "
                    f"with {data['guests']} guests."
                ),
                "link": platform_link(
                    platform,
                    name,
                ),
            }
        )

    return {
        "title": (
            f"{data['event_type']} Party Plan"
        ),

        "summary": (
            f"A practical plan for "
            f"{data['guests']} guests using "
            f"a {data['venue']} venue."
        ),

        "budget": budget,

        "total_estimated": round(
            budget * 0.95,
            2,
        ),

        "savings": round(
            budget * 0.05,
            2,
        ),

        "allocations": [
            {
                "category": category,
                "amount": round(
                    budget * percentage,
                    2,
                ),
                "percentage": percentage * 100,
            }
            for category, percentage
            in allocations
        ],

        "recommendations": recommendations,

        "tips": [
            "Confirm guest count before final catering order.",
            "Keep a small contingency buffer.",
            "Ask vendors what taxes and delivery charges are included.",
        ],

        "disclaimer": (
            "Vendor availability and prices "
            "must be confirmed directly with the provider."
        ),
    }


def fallback_jewelry(
    data: dict,
    image_provided: bool = False,
) -> dict:

    budget = float(data["budget"])

    occasion = data["occasion"]

    style = data["style"]

    items = [
        (
            "Minimal Necklace Set",
            "Necklace",
            "Amazon",
            budget * 0.35,
        ),
        (
            "Statement Earrings",
            "Earrings",
            "Flipkart",
            budget * 0.25,
        ),
        (
            "Classic Bracelet",
            "Bracelet",
            "Amazon",
            budget * 0.20,
        ),
        (
            "Elegant Ring",
            "Ring",
            "Flipkart",
            budget * 0.15,
        ),
    ]

    recommendations = []

    for (
        name,
        category,
        platform,
        price,
    ) in items:

        recommendations.append(
            {
                "name": name,
                "category": category,
                "platform": platform,
                "estimated_price": round(
                    price,
                    2,
                ),
                "reason": (
                    f"Matches a {style} "
                    f"preference for {occasion}."
                ),
                "link": platform_link(
                    platform,
                    name,
                ),
            }
        )

    total = round(
        sum(
            item["estimated_price"]
            for item in recommendations
        ),
        2,
    )

    image_message = (
        " Outfit image was considered."
        if image_provided
        else
        " Add an outfit image for visual color matching."
    )

    return {
        "title": "Jewelry Match Plan",

        "summary": (
            f"{style} jewelry ideas for "
            f"{occasion}."
            f"{image_message}"
        ),

        "budget": budget,

        "total_estimated": total,

        "savings": max(
            0,
            round(
                budget - total,
                2,
            ),
        ),

        "allocations": [
            {
                "category": "Necklace",
                "amount": budget * 0.35,
                "percentage": 35,
            },
            {
                "category": "Earrings",
                "amount": budget * 0.25,
                "percentage": 25,
            },
            {
                "category": "Bracelet",
                "amount": budget * 0.20,
                "percentage": 20,
            },
            {
                "category": "Ring",
                "amount": budget * 0.15,
                "percentage": 15,
            },
            {
                "category": "Buffer",
                "amount": budget * 0.05,
                "percentage": 5,
            },
        ],

        "recommendations": recommendations,

        "tips": [
            "Match metal tone with the outfit and occasion.",
            "Avoid over-accessorizing when the outfit is heavily embellished.",
            "Verify material, size and return policy before purchase.",
        ],

        "disclaimer": (
            "AI suggestions are style guidance. "
            "Verify product materials, sizes and "
            "current prices on the retailer page."
        ),
    }