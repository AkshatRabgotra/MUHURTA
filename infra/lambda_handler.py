"""AWS Lambda handler for scheduled EventBridge invocation of Muhurta reminder processing."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any

# Ensure backend app is in sys.path when deployed to AWS Lambda
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.reminder_service import run_due_reminders


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda entry point triggered by AWS EventBridge rule (e.g. every 1 minute)."""
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    result = loop.run_until_complete(run_due_reminders())

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Due reminders processed successfully",
            "stats": result,
        }),
    }


if __name__ == "__main__":
    res = handler({}, None)
    print(res)
