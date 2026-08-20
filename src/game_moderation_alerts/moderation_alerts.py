"""The moderation decision that controls on-call SMS alerts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .infrai_sms import SmsSendRequest, SmsSendResult


class AssetKind(str, Enum):
    EMBLEM = "emblem"
    MAP = "map"
    VOICE_LINE = "voice_line"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class QueueState(str, Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    RESOLVED = "resolved"


@dataclass(frozen=True)
class PlayerAsset:
    asset_id: str
    player_id: str
    kind: AssetKind
    display_name: str


@dataclass(frozen=True)
class LiveEvent:
    event_id: str
    region: str
    concurrent_players: int


@dataclass(frozen=True)
class ModerationQueueItem:
    queue_id: str
    asset: PlayerAsset
    event: LiveEvent
    risk: RiskLevel
    state: QueueState


@dataclass(frozen=True)
class AlertOutcome:
    action: str
    queue_id: str
    message_id: str | None = None


class SmsSender(Protocol):
    def send(self, payload: SmsSendRequest, *, idempotency_key: str) -> SmsSendResult:
        raise RuntimeError("Protocol methods are supplied by the sender")


def send_moderation_alert(
    item: ModerationQueueItem,
    on_call_phone: str,
    sender: SmsSender,
) -> AlertOutcome:
    """Wake a moderator only for pending, high-risk player content."""
    if item.state is not QueueState.PENDING or item.risk is not RiskLevel.HIGH:
        return AlertOutcome(action="no_alert", queue_id=item.queue_id)

    message = (
        f"Moderation alert: {item.asset.kind.value} '{item.asset.display_name}' "
        f"from player {item.asset.player_id} is high risk in {item.event.region}; "
        f"queue item {item.queue_id}."
    )
    result = sender.send(
        SmsSendRequest(to=on_call_phone, body=message),
        idempotency_key=f"moderation-alert:{item.queue_id}",
    )
    return AlertOutcome(
        action="sms_sent",
        queue_id=item.queue_id,
        message_id=result.message_id,
    )
