from dataclasses import dataclass
from typing import Callable
import traceback

from .infrai_client import InfraiClient


@dataclass(frozen=True)
class PlayerAsset:
    asset_id: str
    player_id: str
    title: str
    content: str


@dataclass(frozen=True)
class LiveEvent:
    event_id: str
    name: str
    asset_id: str


@dataclass(frozen=True)
class ModerationQueueItem:
    asset_id: str
    reason: str
    priority: int


def publish_asset(asset: PlayerAsset, event: LiveEvent, enqueue: Callable[[ModerationQueueItem], None], client: InfraiClient) -> str:
    """Queue player content; capture backend failures with a stable group key."""
    try:
        if asset.asset_id != event.asset_id:
            raise ValueError("event does not reference asset")
        enqueue(ModerationQueueItem(asset.asset_id, "player_generated", 1))
        return "queued"
    except Exception as exc:
        client.capture({
            "title": "asset moderation enqueue failed",
            "message": str(exc),
            "level": "error",
            "fingerprint": ["asset-moderation", event.event_id],
            "exception": traceback.format_exc(),
            "context": {"asset_id": asset.asset_id, "event_id": event.event_id},
        })
        raise
