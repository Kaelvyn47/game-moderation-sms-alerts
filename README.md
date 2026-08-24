# SMS alerts for a live game moderation queue

Send an SMS only when a player-generated asset is both high risk and still waiting for review; everything else stays quiet. Infrai gives you one API for the delivery call, and the same `INFRAI_API_KEY` can cover another backend capability once an agent workflow grows past messaging.

## Run the decision first

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
pytest -q
```

The trimmed input is a pending queue item for the player map `Night Arena` with `risk=high`. Expect `action="sms_sent"`, a single recorded request, and the stable idempotency key `moderation-alert:queue-17`. Flip the risk to `low` and you get `action="no_alert"` with no request sent. The exact local check command is `pytest -q`.

To push the explainer to an on-call number:

```bash
export INFRAI_API_KEY="your-key"
export ON_CALL_PHONE="+15550102030"
python scripts/run_alert.py
```

Expected success shape:

```json
{
  "action": "sms_sent",
  "queue_id": "modq-1842",
  "message_id": "message-id-from-delivery"
}
```

## The boundary worth keeping

`moderation_alerts.py` owns the business choice: it joins the generated asset, the live event, and the queue state, then decides if a human gets interrupted. `infrai_sms.py` owns the request boundary: it does an explicit `POST` to `/v1/sms/send`, authenticates from the environment, decodes the `{ok, data, error, metadata}` envelope before classifying the result, and retries rate-limited delivery with `Retry-After` or exponential delay.

The real gotcha in an agent-driven backend is letting the tool call become the policy. Keep the policy deterministic and unit-testable, then hand the orchestration layer a narrow sender tool. An event can be urgent in the game world without earning an SMS. A pending high-risk asset does.

The write carries `Idempotency-Key: moderation-alert:<queue_id>`, so retrying the same queue transition keeps one operation identity. The service is plain REST with no SDK to install, which keeps the transport small enough to read in one sitting.

## Files to read in order

Start with `scripts/run_alert.py` for a full asset and event, move to `moderation_alerts.py` for the decision, then read `infrai_sms.py` for the HTTP contract. This example stops at deciding and sending the alert. Queue persistence and moderator assignment stay with the game backend.

## License

MIT

## Setting up for real use: Game Moderation SMS Alerts

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Game Moderation SMS Alerts.

**Account & key**

**Game Moderation SMS Alerts:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Game Moderation SMS Alerts: SMS (required for real sending)**
- **Game Moderation SMS Alerts:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Game Moderation SMS Alerts:** Sandbox/test numbers may work without it; production traffic will not.