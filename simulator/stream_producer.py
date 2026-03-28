"""
FraudLens — Redis Stream Producer
Publishes generated transactions to a Redis Stream
so the scoring engine can consume them in real-time.
"""

import sys
import json
import asyncio
import time

import redis.asyncio as aioredis

# Add project root to path
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[1]))

from simulator.generator import generate_transaction
from app.config import settings


STREAM_NAME = "stream:transactions"


async def load_users_from_db() -> list[dict]:
    """Load all user profiles from PostgreSQL."""
    from sqlalchemy import select
    from app.db.session import async_session
    from app.models.user import User

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

        return [
            {
                "id": str(u.id),
                "name": u.name,
                "email": u.email,
                "home_latitude": u.home_latitude,
                "home_longitude": u.home_longitude,
                "home_country": u.home_country,
                "avg_transaction_amount": u.avg_transaction_amount,
                "risk_profile": u.risk_profile,
                "profile_type": u.profile_type,
                "account_age_days": u.account_age_days,
            }
            for u in users
        ]


async def produce_transactions(
    tps: int = 10,
    fraud_rate: float = 0.02,
    duration_seconds: int | None = None,
):
    """
    Continuously generate transactions and publish to Redis Stream.

    Args:
        tps: Transactions per second to generate
        fraud_rate: Probability of fraud (0.02 = 2%)
        duration_seconds: How long to run (None = forever)
    """
    print(f"Loading users from database...")
    users = await load_users_from_db()

    if not users:
        print("❌ No users found. Run seed_service first.")
        return

    print(f"✅ Loaded {len(users)} users")
    print(f"📡 Starting stream producer: {tps} TPS, {fraud_rate*100:.1f}% fraud rate")
    print(f"📺 Stream: {STREAM_NAME}")
    print(f"⏱️  Duration: {'infinite' if duration_seconds is None else f'{duration_seconds}s'}")
    print(f"Press Ctrl+C to stop\n")

    redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    total_sent = 0
    total_fraud = 0
    start_time = time.time()
    interval = 1.0 / tps

    try:
        while True:
            # Check duration
            elapsed = time.time() - start_time
            if duration_seconds and elapsed >= duration_seconds:
                break

            # Generate and publish one transaction
            user = users[total_sent % len(users)]
            txn = generate_transaction(user, fraud_rate)

            # Publish to Redis Stream
            await redis.xadd(
                STREAM_NAME,
                {"data": json.dumps(txn)},
                maxlen=100000,  # Keep last 100K transactions in stream
            )

            total_sent += 1
            if txn["is_fraud"]:
                total_fraud += 1

            # Progress log every 100 transactions
            if total_sent % 100 == 0:
                fraud_pct = (total_fraud / total_sent * 100) if total_sent > 0 else 0
                rate = total_sent / elapsed if elapsed > 0 else 0
                print(
                    f"📊 Sent: {total_sent:,} | "
                    f"Fraud: {total_fraud} ({fraud_pct:.1f}%) | "
                    f"Rate: {rate:.1f} TPS | "
                    f"Elapsed: {elapsed:.0f}s"
                )

            await asyncio.sleep(interval)

    except KeyboardInterrupt:
        print(f"\n\n🛑 Stopped by user")
    finally:
        elapsed = time.time() - start_time
        fraud_pct = (total_fraud / total_sent * 100) if total_sent > 0 else 0
        print(f"\n{'='*50}")
        print(f"📈 Final Stats:")
        print(f"   Total transactions: {total_sent:,}")
        print(f"   Fraudulent: {total_fraud:,} ({fraud_pct:.1f}%)")
        print(f"   Duration: {elapsed:.1f}s")
        print(f"   Avg rate: {total_sent/elapsed:.1f} TPS")
        print(f"{'='*50}")

        await redis.close()


async def main():
    """Entry point when running as script."""
    await produce_transactions(
        tps=10,               # 10 transactions per second
        fraud_rate=0.02,      # 2% fraud
        duration_seconds=60,  # Run for 60 seconds (600 transactions)
    )


if __name__ == "__main__":
    # Run from backend/ directory:
    # python -m simulator.stream_producer
    asyncio.run(main())