"""Run one high-risk moderation alert from input to delivery."""

from __future__ import annotations

import json
import os

from game_moderation_alerts import (
    AssetKind,
    LiveEvent,
    ModerationQueueItem,
    PlayerAsset,
    QueueState,
    RiskLevel,
    send_moderation_alert,
)
from game_moderation_alerts.infrai_sms import InfraiSmsClient


def main() -> None:
    api_key = os.environ["INFRAI_API_KEY"]
    phone = os.environ["ON_CALL_PHONE"]
    item = ModerationQueueItem(
        queue_id="modq-1842",
        asset=PlayerAsset(
            asset_id="asset-771",
            player_id="player-92",
            kind=AssetKind.EMBLEM,
            display_name="Ranked Banner",
        ),
        event=LiveEvent(
            event_id="event-44",
            region="ap-east",
            concurrent_players=18200,
        ),
        risk=RiskLevel.HIGH,
        state=QueueState.PENDING,
    )
    outcome = send_moderation_alert(item, phone, InfraiSmsClient(api_key))
    print(json.dumps(outcome.__dict__, indent=2))


if __name__ == "__main__":
    main()
