"""
FraudLens — Transaction Generator
Generates realistic transactions for each user profile type
and injects fraud at a configurable rate.
"""

import random
import uuid
from datetime import datetime, timezone

from simulator.fraud_patterns import generate_fraud_transaction


# ── Merchant Pools by Category ───────────────────────────
MERCHANTS = {
    "food": [
        "Tim Hortons", "Starbucks", "McDonald's", "Subway",
        "Pizza Pizza", "A&W", "Popeyes", "Wendy's",
    ],
    "grocery": [
        "Loblaws", "Metro", "Sobeys", "No Frills",
        "Walmart Grocery", "Costco", "FreshCo", "Food Basics",
    ],
    "gas": [
        "Petro-Canada", "Shell", "Esso", "Canadian Tire Gas",
    ],
    "shopping": [
        "Amazon.ca", "Walmart", "Canadian Tire", "Hudson's Bay",
        "Best Buy", "Shoppers Drug Mart", "Dollarama",
    ],
    "transit": [
        "Presto Card Reload", "TTC", "GO Transit", "Uber",
    ],
    "entertainment": [
        "Netflix", "Spotify", "Cineplex", "Disney+",
    ],
    "electronics": [
        "Best Buy", "Canada Computers", "Apple Store", "Memory Express",
    ],
    "travel": [
        "Air Canada", "WestJet", "Booking.com", "Airbnb",
        "Marriott", "Hilton",
    ],
    "dining": [
        "The Keg", "Swiss Chalet", "Moxie's", "Earls",
        "Boston Pizza", "Montana's",
    ],
    "utilities": [
        "Bell Canada", "Rogers", "Telus", "Hydro One",
        "Enbridge Gas",
    ],
}

# ── Profile Spending Patterns ────────────────────────────
PROFILE_PATTERNS = {
    "student": {
        "categories": ["food", "transit", "entertainment", "grocery"],
        "weights": [0.35, 0.25, 0.20, 0.20],
        "amount_multiplier": (0.3, 1.5),
        "online_ratio": 0.3,
    },
    "professional": {
        "categories": ["food", "grocery", "shopping", "gas", "dining", "utilities"],
        "weights": [0.20, 0.20, 0.20, 0.15, 0.15, 0.10],
        "amount_multiplier": (0.5, 2.0),
        "online_ratio": 0.35,
    },
    "business_traveler": {
        "categories": ["travel", "dining", "food", "shopping", "entertainment"],
        "weights": [0.30, 0.25, 0.20, 0.15, 0.10],
        "amount_multiplier": (0.5, 3.0),
        "online_ratio": 0.4,
    },
    "retiree": {
        "categories": ["grocery", "utilities", "food", "shopping"],
        "weights": [0.35, 0.25, 0.25, 0.15],
        "amount_multiplier": (0.4, 1.8),
        "online_ratio": 0.15,
    },
    "affluent": {
        "categories": ["shopping", "dining", "travel", "electronics", "entertainment"],
        "weights": [0.25, 0.25, 0.20, 0.15, 0.15],
        "amount_multiplier": (0.5, 4.0),
        "online_ratio": 0.45,
    },
}


def generate_legit_transaction(user: dict) -> dict:
    """
    Generate a realistic legitimate transaction for a user.
    Spending pattern matches their profile type.
    """
    profile = user.get("profile_type", "professional")
    pattern = PROFILE_PATTERNS.get(profile, PROFILE_PATTERNS["professional"])

    # Pick a category based on weights
    category = random.choices(pattern["categories"], weights=pattern["weights"], k=1)[0]

    # Pick a merchant from that category
    merchant_name = random.choice(MERCHANTS[category])

    # Calculate amount based on user's average and profile pattern
    min_mult, max_mult = pattern["amount_multiplier"]
    amount = round(
        user["avg_transaction_amount"] * random.uniform(min_mult, max_mult), 2
    )
    amount = max(1.0, amount)  # Minimum $1

    # Location: near user's home with small random offset
    lat = user["home_latitude"] + random.uniform(-0.03, 0.03)
    lon = user["home_longitude"] + random.uniform(-0.03, 0.03)

    # Online or in-person
    is_online = random.random() < pattern["online_ratio"]

    return {
        "amount": amount,
        "currency": "CAD",
        "merchant_name": merchant_name,
        "merchant_category": category,
        "card_type": random.choice(["visa", "mastercard", "amex", "debit"]),
        "latitude": round(lat, 6),
        "longitude": round(lon, 6),
        "country_code": "CA",
        "is_online": is_online,
        "fraud_type": None,
        "is_fraud": False,
    }


def generate_transaction(user: dict, fraud_rate: float = 0.02) -> dict:
    """
    Generate a single transaction for a user.

    Args:
        user: User profile dict
        fraud_rate: Probability of fraud (default 2%)

    Returns:
        Transaction dict ready for Redis Stream / PostgreSQL
    """
    # Decide if this transaction is fraudulent
    if random.random() < fraud_rate:
        txn = generate_fraud_transaction(user)
    else:
        txn = generate_legit_transaction(user)

    # Add common fields
    txn["id"] = str(uuid.uuid4())
    txn["user_id"] = user["id"]
    txn["user_name"] = user["name"]
    txn["currency"] = txn.get("currency", "CAD")
    txn["created_at"] = datetime.now(timezone.utc).isoformat()

    return txn


def generate_batch(users: list[dict], count: int = 100, fraud_rate: float = 0.02) -> list[dict]:
    """
    Generate a batch of transactions across random users.
    """
    transactions = []
    for _ in range(count):
        user = random.choice(users)
        txn = generate_transaction(user, fraud_rate)
        transactions.append(txn)
    return transactions