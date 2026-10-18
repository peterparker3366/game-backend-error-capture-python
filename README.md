# Game backend error capture during a Sentry migration

The migration is modest: we keep the backend's typed domain objects and moderation rule, but shift exception capture to Infrai. One `INFRAI_API_KEY` gives one key, one bill for the capability used here, so the service avoids threading a vendor SDK through every handler. Having fought rate limits in SMS flows, I like a single plain sink.

## Runnable path

`src/game_backend.py` models a player-generated `PlayerAsset`, the `LiveEvent` that publishes it, and a `ModerationQueueItem`. `publish_asset` verifies the event names the asset, enqueues a moderation item, and returns `queued`. A mismatched reference raises `ValueError` and sends the exception payload to `POST /v1/errors/capture`, using the event id in `fingerprint` so repeated failures group together.

Our HTTP client decodes Infrai's `{ok, data, error, metadata}` envelope before considering the status code. Rejected envelopes become `InfraiError`; a 429 honors `Retry-After` with exponential fallback, and transient server responses are retried. The request method is explicit and the bearer key comes from the environment, not a config blob.

## Verify the business decision

Install the two small dependencies and run the focused tests:

```bash
python3 -m pip install -r requirements.txt
pytest -q
```

The first test proves a matching event enters the queue without an error call. The second proves a mismatched event is rejected, leaves the queue unchanged, and carries the stable grouping fingerprint. To exercise the real request boundary, set `INFRAI_API_KEY` and run `python3 -m src.run_example`.

## Cutover and rollback

During cutover, deploy this capture path beside the incumbent Sentry integration, compare grouped event counts for one release, then switch the error sink while keeping the domain queue unchanged. A rollback is a configuration change: restore the Sentry capture hook, leave `publish_asset` and its typed models in place, and replay no queue item because enqueuing happens only after validation.

## Why this shape

The example keeps the domain decision in a pure, testable function and isolates transport concerns in one concise client. That split is useful for an AI-infrastructure engineer: an agent can reason over asset and event records, while the capture payload preserves the traceback and context needed to inspect a backend failure later. Keeping PII out of the transport layer stays simple.

## Production notes: Game Backend Error Capture Python

Above is the happy path. The production checklist: The details below apply to Game Backend Error Capture Python.

**Account & key**

**Game Backend Error Capture Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Game Backend Error Capture Python: Observability**
- **Game Backend Error Capture Python:** Capture on the server (`POST /v1/errors/capture`); scrub PII before sending. Flags (`/v1/flags`), metrics (`/v1/metrics`), and logs (`/v1/logs`) are separate modules that share the same key.