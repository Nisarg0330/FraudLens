"""
FraudLens — Synthetic User Profile Generator
Creates 1,000 realistic Canadian user profiles with 5 spending types.
"""

import random
import uuid

# ── Canadian Cities with Coordinates ─────────────────────
CANADIAN_CITIES = [
    {"city": "Toronto", "lat": 43.6532, "lon": -79.3832},
    {"city": "Brampton", "lat": 43.7315, "lon": -79.7624},
    {"city": "Mississauga", "lat": 43.5890, "lon": -79.6441},
    {"city": "Vancouver", "lat": 49.2827, "lon": -123.1207},
    {"city": "Montreal", "lat": 45.5017, "lon": -73.5673},
    {"city": "Calgary", "lat": 51.0447, "lon": -114.0719},
    {"city": "Edmonton", "lat": 53.5461, "lon": -113.4938},
    {"city": "Ottawa", "lat": 45.4215, "lon": -75.6972},
    {"city": "Winnipeg", "lat": 49.8951, "lon": -97.1384},
    {"city": "Hamilton", "lat": 43.2557, "lon": -79.8711},
    {"city": "Kitchener", "lat": 43.4516, "lon": -80.4925},
    {"city": "London", "lat": 42.9849, "lon": -81.2453},
    {"city": "Halifax", "lat": 44.6488, "lon": -63.5752},
    {"city": "Victoria", "lat": 48.4284, "lon": -123.3656},
    {"city": "Waterloo", "lat": 43.4643, "lon": -80.5204},
    {"city": "Surrey", "lat": 49.1913, "lon": -122.8490},
    {"city": "Markham", "lat": 43.8561, "lon": -79.3370},
    {"city": "Richmond Hill", "lat": 43.8828, "lon": -79.4403},
    {"city": "Vaughan", "lat": 43.8361, "lon": -79.4983},
    {"city": "Oakville", "lat": 43.4675, "lon": -79.6877},
]

# ── First & Last Names ───────────────────────────────────
FIRST_NAMES = [
    "Aarav", "Priya", "James", "Sarah", "Wei", "Fatima", "Liam", "Emma",
    "Muhammad", "Olivia", "Arjun", "Chloe", "Ethan", "Maya", "Noah",
    "Aisha", "Lucas", "Sophia", "Dev", "Isabella", "Alexander", "Mia",
    "Daniel", "Amara", "Benjamin", "Zara", "William", "Ananya", "Henry",
    "Leah", "Jack", "Noor", "Owen", "Riya", "Nathan", "Hannah", "Ryan",
    "Simran", "Andrew", "Jasmine", "Michael", "Neha", "David", "Aliya",
    "Kevin", "Tara", "Chris", "Meera", "Jason", "Pooja",
]

LAST_NAMES = [
    "Patel", "Singh", "Chen", "Wilson", "Kim", "Ahmed", "Brown", "Lee",
    "Martin", "Thompson", "Garcia", "Wang", "Ali", "Taylor", "Sharma",
    "Anderson", "Li", "Hassan", "Moore", "Clark", "Nguyen", "White",
    "Robinson", "Khan", "Walker", "Young", "Hall", "Das", "Scott",
    "Green", "Baker", "Adams", "Nelson", "Hill", "Kaur", "Mitchell",
    "Roberts", "Campbell", "Phillips", "Evans", "Turner", "Parker",
    "Collins", "Edwards", "Stewart", "Malik", "Murphy", "Cook", "Gupta",
    "Rivera",
]

# ── Profile Types ────────────────────────────────────────
PROFILE_CONFIGS = {
    "student": {
        "avg_amount_range": (8, 35),
        "account_age_range": (90, 730),
        "risk_profile": "low",
        "weight": 0.25,  # 25% of users
    },
    "professional": {
        "avg_amount_range": (30, 150),
        "account_age_range": (365, 2555),
        "risk_profile": "low",
        "weight": 0.35,  # 35% of users
    },
    "business_traveler": {
        "avg_amount_range": (80, 400),
        "account_age_range": (365, 1825),
        "risk_profile": "medium",
        "weight": 0.15,  # 15% of users
    },
    "retiree": {
        "avg_amount_range": (20, 100),
        "account_age_range": (1825, 7300),
        "risk_profile": "low",
        "weight": 0.15,  # 15% of users
    },
    "affluent": {
        "avg_amount_range": (150, 1500),
        "account_age_range": (730, 3650),
        "risk_profile": "medium",
        "weight": 0.10,  # 10% of users
    },
}


def generate_users(count: int = 1000) -> list[dict]:
    """
    Generate synthetic user profiles.

    Returns a list of dicts ready to be inserted into PostgreSQL.
    Each user has:
    - Unique UUID, name, email
    - Home location (real Canadian city + slight random offset)
    - Spending profile (student/professional/business/retiree/affluent)
    - Average transaction amount matching their profile
    """
    users = []
    used_emails = set()

    # Calculate how many users per profile type
    profile_counts = {}
    remaining = count
    for profile_type, config in PROFILE_CONFIGS.items():
        n = int(count * config["weight"])
        profile_counts[profile_type] = n
        remaining -= n
    # Add remaining to professional (largest group)
    profile_counts["professional"] += remaining

    for profile_type, n in profile_counts.items():
        config = PROFILE_CONFIGS[profile_type]

        for _ in range(n):
            # Generate unique name and email
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            name = f"{first} {last}"

            # Ensure unique email
            base_email = f"{first.lower()}.{last.lower()}"
            email = f"{base_email}@example.com"
            counter = 1
            while email in used_emails:
                email = f"{base_email}{counter}@example.com"
                counter += 1
            used_emails.add(email)

            # Pick a Canadian city and add slight randomness
            city = random.choice(CANADIAN_CITIES)
            lat_offset = random.uniform(-0.05, 0.05)
            lon_offset = random.uniform(-0.05, 0.05)

            # Generate profile
            user = {
                "id": str(uuid.uuid4()),
                "name": name,
                "email": email,
                "home_latitude": round(city["lat"] + lat_offset, 6),
                "home_longitude": round(city["lon"] + lon_offset, 6),
                "home_country": "CA",
                "avg_transaction_amount": round(
                    random.uniform(*config["avg_amount_range"]), 2
                ),
                "risk_profile": config["risk_profile"],
                "profile_type": profile_type,
                "account_age_days": random.randint(*config["account_age_range"]),
            }
            users.append(user)

    random.shuffle(users)
    return users


if __name__ == "__main__":
    """Quick test — run this file directly to see sample output."""
    users = generate_users(10)
    for u in users:
        print(f"{u['name']:25s} | {u['profile_type']:18s} | ${u['avg_transaction_amount']:>8.2f} avg")
    print(f"\nGenerated {len(users)} users")