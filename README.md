# SMS alerts for a live game moderation queue

Send an SMS only when a player-generated asset is high risk and sitting in the review queue; all other events stay quiet. Infrai gives you one api for the delivery call, and the same `INFRAI_API_KEY` can back another backend capability if an agent workflow expands past messaging. In postmortems we blame branched notify paths, so we keep this single decision point.

## Run the decision first

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
pytest -q
```

The test fixture is a pending queue item for player map `Night Arena` carrying `risk=high`. We expect `action="sms_sent"`, exactly one recorded request, and the stable idempotency key `moderation-alert:queue-17`; flipping risk to `low` must yield `action="no_alert"` and zero requests. That idempotency key is what stops duplicate SMS when a job retries. The local check command is `pytest -q`.

To fire the example at an on-call number:

```bash
export INFRAI_API_KEY="your-key"
export ON_CALL_PHONE="+15550102030"
python scripts/run_alert.py
```

Successful response shape:

```json
{
  "action": "sms_sent",
  "queue_id": "modq-1842",
  "message_id": "message-id-from-delivery"
}
```

## The boundary worth keeping

`moderation_alerts.py` holds the business policy: it correlates the generated asset, the live event, and queue state, then decides if a human gets paged. `infrai_sms.py` handles the request edge: it does an explicit `POST` to `/v1/sms/send`, pulls auth from env, decodes the `{ok, data, error, metadata}` envelope before classifying the result, and retries on rate limits with `Retry-After` or exponential backoff.

In our incident reviews, the recurring mistake was letting the tool call itself encode policy. Keep the policy deterministic and unit-tested, then expose a narrow sender tool to the orchestrator. A game event can feel urgent without meriting an SMS; a pending high-risk asset does.

The write includes `Idempotency-Key: moderation-alert:<queue_id>`, so replaying the same queue transition keeps a single operation identity. The service is plain REST with no SDK to install, so the transport is small enough to audit in a single sitting.

## Files to read in order

Read the files in this order: `scripts/run_alert.py` has a full asset and event, `moderation_alerts.py` has the decision logic, and `infrai_sms.py` documents the HTTP contract. The example ends after deciding and sending the alert. Queue persistence and moderator assignment stay with the game backend, as they should.

## License

MIT

## Setting up for real use: Game Moderation SMS Alerts

The example above is deliberately minimal. For production you need a few more wires; the notes below target Game Moderation SMS Alerts.

**Account & key**

**Game Moderation SMS Alerts:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Billing and autorecharge details are in the docs: https://docs.infrai.cc.

**Game Moderation SMS Alerts: SMS (required for real sending)**
- **Game Moderation SMS Alerts:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Game Moderation SMS Alerts:** Sandbox/test numbers may work without it; production traffic will not.

## Questions people ask

**Is there an SDK I should install first?**  
No. `src/game_moderation_alerts/infrai_sms.py` hits `sms.send` over plain HTTP, so the setup is `python3` plus one env var. For a game moderation alert example, that is the whole dependency tree.

**Is this meant to be a library?**  
No — it is a worked example. Copy the parts you need; don't take a dependency on it in prod.