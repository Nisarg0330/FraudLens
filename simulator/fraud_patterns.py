"""
FraudLens — Fraud Pattern Definitions
5 fraud attack types, each testing different ML model strengths.
"""

import random
import uuid
from datetime import datetime, timezone


# ── Fraud Scenario Generators ────────────────────────────

def card_cloning_attack(user: dict) -> dict:
    """
    CARD CLONING: Card used simultaneously in two far-apart locations.
    The real user is at home, the clone is used 1000+ km away.
    Tests: Autoencoder + geo_velocity feature.
    """
    # Pick a location far from user's home
    far_locations = [
        {"lat": 25.7617, "lon": -80.1918, "country": "US", "city": "Miami"},
        {"lat": 51.5074, "lon": -0.1278, "country": "GB", "city": "London"},
        {"lat": 40.7128, "lon": -74.0060, "country": "US", "city": "New York"},
        {"lat": 48.8566, "lon": 2.3522, "country": "FR", "city": "Paris"},
        {"lat": 35.6762, "lon": 139.6503, "country": "JP", "city": "Tokyo"},
        {"lat": 19.4326, "lon": -99.1332, "country": "MX", "city": "Mexico City"},
    ]
    location = random.choice(far_locations)

    # Fraudster spends more than user's average
    amount = round(random.uniform(200, 2000), 2)

    merchants = [
        ("Electronics Express", "electronics"),
        ("Luxury Watches Co", "luxury"),
        ("Premium Fashion", "clothing"),
        ("Tech Galaxy", "electronics"),
        ("Gold & Diamond", "jewelry"),
    ]
    merchant = random.choice(merchants)

    return {
        "amount": amount,
        "merchant_name": merchant[0],
        "merchant_category": merchant[1],
        "latitude": location["lat"],
        "longitude": location["lon"],
        "country_code": location["country"],
        "is_online": False,
        "card_type": random.choice(["visa", "mastercard"]),
        "fraud_type": "card_cloning",
        "is_fraud": True,
    }


def account_takeover_attack(user: dict) -> dict:
    """
    ACCOUNT TAKEOVER: Attacker gains access, immediately changes spending.
    Different categories, higher amounts, unusual hours.
    Tests: LightGBM + behavioral deviation features.
    """
    # Spend way more than usual
    amount = round(user["avg_transaction_amount"] * random.uniform(5, 15), 2)

    # Categories the user wouldn't normally use
    unusual_merchants = [
        ("CryptoExchange Pro", "cryptocurrency"),
        ("Gift Cards Unlimited", "gift_cards"),
        ("Wire Transfer Services", "financial"),
        ("Foreign Currency Exchange", "financial"),
        ("Premium Gaming Credits", "gaming"),
    ]
    merchant = random.choice(unusual_merchants)

    # Use user's home location (attacker has the account, not the card)
    return {
        "amount": amount,
        "merchant_name": merchant[0],
        "merchant_category": merchant[1],
        "latitude": user["home_latitude"] + random.uniform(-0.01, 0.01),
        "longitude": user["home_longitude"] + random.uniform(-0.01, 0.01),
        "country_code": "CA",
        "is_online": True,  # Usually online
        "card_type": random.choice(["visa", "mastercard", "amex"]),
        "fraud_type": "account_takeover",
        "is_fraud": True,
    }


def velocity_attack(user: dict) -> dict:
    """
    VELOCITY ATTACK: Rapid small transactions testing card validity.
    Many $5-20 charges at different merchants within minutes.
    Tests: Isolation Forest + txn_count rolling features.
    """
    amount = round(random.uniform(2, 25), 2)

    test_merchants = [
        ("Corner Store #127", "convenience"),
        ("Gas Station Quick Pay", "gas"),
        ("Vending Machine Corp", "vending"),
        ("Parking Meter Digital", "parking"),
        ("Coffee Express Kiosk", "food"),
        ("Newspaper Stand Auto", "retail"),
    ]
    merchant = random.choice(test_merchants)

    return {
        "amount": amount,
        "merchant_name": merchant[0],
        "merchant_category": merchant[1],
        "latitude": user["home_latitude"] + random.uniform(-0.1, 0.1),
        "longitude": user["home_longitude"] + random.uniform(-0.1, 0.1),
        "country_code": "CA",
        "is_online": False,
        "card_type": "visa",
        "fraud_type": "velocity_attack",
        "is_fraud": True,
    }


def first_party_fraud(user: dict) -> dict:
    """
    FIRST-PARTY FRAUD: User makes a legit-looking purchase, then disputes it.
    Subtle pattern changes before the dispute.
    Tests: LightGBM + subtle feature engineering.
    """
    # Slightly above average, specific categories
    amount = round(user["avg_transaction_amount"] * random.uniform(2, 4), 2)

    dispute_merchants = [
        ("Online Marketplace Plus", "ecommerce"),
        ("Digital Subscription Pro", "subscription"),
        ("Electronics Direct Ship", "electronics"),
        ("Fashion Forward Online", "clothing"),
    ]
    merchant = random.choice(dispute_merchants)

    return {
        "amount": amount,
        "merchant_name": merchant[0],
        "merchant_category": merchant[1],
        "latitude": user["home_latitude"] + random.uniform(-0.02, 0.02),
        "longitude": user["home_longitude"] + random.uniform(-0.02, 0.02),
        "country_code": "CA",
        "is_online": True,
        "card_type": random.choice(["visa", "mastercard"]),
        "fraud_type": "first_party_fraud",
        "is_fraud": True,
    }


def merchant_fraud(user: dict) -> dict:
    """
    MERCHANT FRAUD: Compromised merchant runs small charges across many cards.
    Same merchant, many different users, small amounts.
    Tests: Ensemble + merchant pattern analysis.
    """
    amount = round(random.uniform(5, 50), 2)

    # Same compromised merchant for all
    return {
        "amount": amount,
        "merchant_name": "QuickMart Global #8832",
        "merchant_category": "retail",
        "latitude": 43.6532 + random.uniform(-0.01, 0.01),
        "longitude": -79.3832 + random.uniform(-0.01, 0.01),
        "country_code": "CA",
        "is_online": False,
        "card_type": random.choice(["visa", "mastercard", "debit"]),
        "fraud_type": "merchant_fraud",
        "is_fraud": True,
    }


# ── Fraud Pattern Registry ───────────────────────────────
FRAUD_PATTERNS = {
    "card_cloning": card_cloning_attack,
    "account_takeover": account_takeover_attack,
    "velocity_attack": velocity_attack,
    "first_party_fraud": first_party_fraud,
    "merchant_fraud": merchant_fraud,
}


def generate_fraud_transaction(user: dict) -> dict:
    """Pick a random fraud type and generate a fraudulent transaction."""
    fraud_type = random.choice(list(FRAUD_PATTERNS.keys()))
    return FRAUD_PATTERNS[fraud_type](user)