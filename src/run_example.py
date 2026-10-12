from .game_backend import LiveEvent, PlayerAsset, publish_asset
from .infrai_client import InfraiClient


def main() -> None:
    queue = []
    asset = PlayerAsset("asset-42", "player-7", "Neon Arena", "arena layout")
    event = LiveEvent("event-9", "weekend-launch", "asset-other")
    try:
        publish_asset(asset, event, queue.append, InfraiClient())
    except ValueError as exc:
        print({"result": "rejected", "error": str(exc), "queued_items": len(queue)})


if __name__ == "__main__":
    main()
