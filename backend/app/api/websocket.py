"""
FraudLens — WebSocket Endpoints
Pushes real-time transaction and alert data to Deep's frontend.
"""

import json
import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config import settings
from app.db.redis import get_redis

router = APIRouter(tags=["WebSocket"])

# Track active WebSocket connections
active_connections: list[WebSocket] = []


@router.websocket("/ws/transactions")
async def ws_transactions(websocket: WebSocket):
    """
    Real-time transaction stream.
    Deep's frontend connects here to show live transactions
    appearing on the dashboard without polling.
    """
    await websocket.accept()
    active_connections.append(websocket)
    print(f"🔌 WebSocket connected. Active: {len(active_connections)}")

    redis = await get_redis()
    last_id = "$"  # Start from newest messages

    try:
        while True:
            # Read from Redis Stream
            messages = await redis.xread(
                {"stream:transactions": last_id},
                count=10,
                block=1000,  # Wait up to 1 second for new data
            )

            if messages:
                for stream_name, stream_messages in messages:
                    for msg_id, msg_data in stream_messages:
                        last_id = msg_id
                        txn_data = json.loads(msg_data["data"])

                        # Push to WebSocket
                        await websocket.send_json({
                            "type": "transaction",
                            "data": txn_data,
                        })

            # Small delay to prevent CPU spinning
            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print(f"🔌 WebSocket disconnected. Active: {len(active_connections)}")
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)
    finally:
        await redis.close()


@router.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket):
    """
    Real-time fraud alert stream.
    Pushes only REVIEW and BLOCK transactions.
    """
    await websocket.accept()
    print(f"🚨 Alert WebSocket connected")

    redis = await get_redis()
    last_id = "$"

    try:
        while True:
            messages = await redis.xread(
                {"stream:transactions": last_id},
                count=10,
                block=1000,
            )

            if messages:
                for stream_name, stream_messages in messages:
                    for msg_id, msg_data in stream_messages:
                        last_id = msg_id
                        txn_data = json.loads(msg_data["data"])

                        # Only push fraud alerts
                        if txn_data.get("is_fraud"):
                            await websocket.send_json({
                                "type": "alert",
                                "data": txn_data,
                            })

            await asyncio.sleep(0.1)

    except WebSocketDisconnect:
        print(f"🚨 Alert WebSocket disconnected")
    except Exception as e:
        print(f"❌ Alert WebSocket error: {e}")
    finally:
        await redis.close()