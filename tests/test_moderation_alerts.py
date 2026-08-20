from game_moderation_alerts import (
    AssetKind,
    LiveEvent,
    ModerationQueueItem,
    PlayerAsset,
    QueueState,
    RiskLevel,
    send_moderation_alert,
)
from game_moderation_alerts.infrai_sms import SmsSendRequest, SmsSendResult


class RecordingSender:
    def __init__(self) -> None:
        self.calls: list[tuple[SmsSendRequest, str]] = []

    def send(self, payload: SmsSendRequest, *, idempotency_key: str) -> SmsSendResult:
        self.calls.append((payload, idempotency_key))
        return SmsSendResult(message_id="msg-accepted", metadata={"route": "primary"})


def queue_item(risk: RiskLevel, state: QueueState = QueueState.PENDING) -> ModerationQueueItem:
    return ModerationQueueItem(
        queue_id="queue-17",
        asset=PlayerAsset("asset-8", "player-4", AssetKind.MAP, "Night Arena"),
        event=LiveEvent("event-3", "eu-west", 6400),
        risk=risk,
        state=state,
    )


def test_high_risk_pending_asset_sends_one_idempotent_alert() -> None:
    sender = RecordingSender()

    outcome = send_moderation_alert(queue_item(RiskLevel.HIGH), "+15550102030", sender)

    assert outcome.action == "sms_sent"
    assert outcome.message_id == "msg-accepted"
    assert len(sender.calls) == 1
    payload, key = sender.calls[0]
    assert payload.to == "+15550102030"
    assert "Night Arena" in payload.message
    assert key == "moderation-alert:queue-17"


def test_low_risk_asset_stays_silent() -> None:
    sender = RecordingSender()

    outcome = send_moderation_alert(queue_item(RiskLevel.LOW), "+15550102030", sender)

    assert outcome.action == "no_alert"
    assert sender.calls == []
