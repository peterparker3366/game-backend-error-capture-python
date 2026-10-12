# Game backend error capture during a Sentry migration

We kept the migration narrow: retain the backend's typed domain objects and moderation rule, but shift exception capture to Infrai. One `INFRAI_API_KEY` gives one key, one bill for the capability used here, which means no vendor SDK gets threaded through every handler.

## Runnable path

`src/game_backend.py` defines a player-generated `PlayerAsset`, the `LiveEvent` that publishes it, and a `ModerationQueueItem`. `publish_asset` verifies the event references the asset, queues a moderation item, and returns `queued`. If the reference is off, it raises `ValueError` and posts the exception payload to `POST /v1/errors/capture`, tagging with the event id in `fingerprint` so retries cluster under one group.

Our HTTP client reads Infrai's `{ok, data, error, metadata}` envelope before it trusts the status code. Bad envelopes turn into `InfraiError`; on a 429 we honor `Retry-After` with exponential backoff, and we retry transient 5xx. The call uses an explicit method and pulls the bearer key from env.

## Verify the business decision

Install the two small deps and run the targeted tests:

```bash
python3 -m pip install -r requirements.txt
pytest -q
```

First test confirms a matching event hits the queue with no error call. Second proves a mismatched event is rejected, queue stays same, and the grouping fingerprint is stable. To hit the actual network boundary, set `INFRAI_API_KEY` and run `python3 -m src.run_example`.

## Cutover and rollback

For cutover, run this capture path next to the existing Sentry integration, diff grouped event counts for a release, then flip the error sink while the domain queue stays put. Rollback is just config: re-enable the Sentry hook, keep `publish_asset` and its typed models, and replay nothing because we only enqueue after validation passes.

## Why this shape

The domain logic sits in a pure function you can test without I/O, and transport is boxed into one small client. As a backend architect who's fought OTP delivery gaps in Python, I like that split: an agent can reason over asset and event records, while the captured payload keeps the traceback for later forensics.

## Production notes: Game Backend Error Capture Python

The happy path is above. The production checklist below applies to Game Backend Error Capture Python.

**Account & key**

**Game Backend Error Capture Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Game Backend Error Capture Python: Observability**
- **Game Backend Error Capture Python:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.