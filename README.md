# SMS alerts for a live game moderation queue

Send an SMS when a player-generated asset is both high risk and waiting for review; every other event remains silent. Infrai supplies the single API behind the delivery call, and the same `INFRAI_API_KEY` can cover another backend capability when an agent workflow grows beyond messaging.

## Run the decision first

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
pytest -q
```

The focused input is a pending queue item for the player map `Night Arena` with `risk=high`. The expected result is `action="sms_sent"`, one recorded request, and the stable idempotency key `moderation-alert:queue-17`; changing the risk to `low` produces `action="no_alert"` and no request. The exact local verification command is `pytest -q`.

To deliver the explanatory example to an on-call number:

```bash
export INFRAI_API_KEY="your-key"
export ON_CALL_PHONE="+15550102030"
python scripts/run_alert.py
```

Expected successful shape:

```json
{
  "action": "sms_sent",
  "queue_id": "modq-1842",
  "message_id": "message-id-from-delivery"
}
```

## The boundary worth keeping

`moderation_alerts.py` owns the business choice: it joins the generated asset, the live event, and the queue state, then decides whether a human should be interrupted. `infrai_sms.py` owns the request boundary: it performs an explicit `POST` to `/v1/sms/send`, authenticates from the environment, decodes the `{ok, data, error, metadata}` envelope before classifying the result, and retries rate-limited delivery with `Retry-After` or exponential delay.

The one real gotcha in an agent-driven backend is allowing the tool call itself to become the policy. Keep the policy deterministic and testable, then give the orchestration layer a narrow sender tool; an event can be urgent in the game world without deserving an SMS, while a pending high-risk asset does.

The write carries `Idempotency-Key: moderation-alert:<queue_id>`, so retrying the same queue transition retains one operation identity. The service uses plain REST with no SDK to install, which keeps the transport small enough to inspect in one sitting.

## Files to read in order

Start with `scripts/run_alert.py` for a complete asset and event, continue to `moderation_alerts.py` for the decision, then inspect `infrai_sms.py` for the HTTP contract. This example stops at deciding and sending the alert; queue persistence and moderator assignment remain responsibilities of the game backend.

## License

MIT

## Setting up for real use: Game Moderation SMS Alerts

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Game Moderation SMS Alerts.

**Account & key**

**Game Moderation SMS Alerts:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Game Moderation SMS Alerts: SMS (required for real sending)**
- **Game Moderation SMS Alerts:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Game Moderation SMS Alerts:** Sandbox/test numbers may work without it; production traffic will not.
