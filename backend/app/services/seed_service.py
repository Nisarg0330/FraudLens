"""
FraudLens — Database Seeding Service
Seeds the database with synthetic user profiles.
"""

import sys
import uuid
import asyncio

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import async_session, engine, Base
from app.models.user import User

# Add project root to path so we can import simulator
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[3]))
from simulator.user_profiles import generate_users


async def seed_users(count: int = 1000) -> int:
    """
    Generate and insert synthetic users into the database.
    Skips if users already exist.
    Returns the number of users created.
    """
    async with async_session() as session:
        # Check if users already exist
        result = await session.execute(select(func.count(User.id)))
        existing_count = result.scalar()

        if existing_count > 0:
            print(f"Database already has {existing_count} users. Skipping seed.")
            return 0

        # Generate users
        print(f"Generating {count} synthetic users...")
        user_dicts = generate_users(count)

        # Insert into database
        users = []
        for u in user_dicts:
            user = User(
                id=uuid.UUID(u["id"]),
                name=u["name"],
                email=u["email"],
                home_latitude=u["home_latitude"],
                home_longitude=u["home_longitude"],
                home_country=u["home_country"],
                avg_transaction_amount=u["avg_transaction_amount"],
                risk_profile=u["risk_profile"],
                profile_type=u["profile_type"],
                account_age_days=u["account_age_days"],
            )
            users.append(user)

        session.add_all(users)
        await session.commit()

        print(f"✅ Seeded {len(users)} users into the database")
        return len(users)


async def main():
    """Run seeding as a standalone script."""
    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    count = await seed_users(1000)
    await engine.dispose()
    return count


if __name__ == "__main__":
    asyncio.run(main())