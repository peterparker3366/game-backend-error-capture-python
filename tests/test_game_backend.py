from unittest.mock import Mock

import pytest

from src.game_backend import LiveEvent, PlayerAsset, publish_asset


def test_matching_event_enters_moderation_queue():
    queue = []
    client = Mock()
    asset = PlayerAsset("a1", "p1", "Castle", "layout")
    event = LiveEvent("e1", "launch", "a1")

    assert publish_asset(asset, event, queue.append, client) == "queued"
    assert queue[0].asset_id == "a1"
    client.capture.assert_not_called()


def test_mismatched_event_is_captured_and_not_queued():
    queue = []
    client = Mock()
    asset = PlayerAsset("a1", "p1", "Castle", "layout")
    event = LiveEvent("e1", "launch", "other")

    with pytest.raises(ValueError):
        publish_asset(asset, event, queue.append, client)
    assert queue == []
    assert client.capture.call_args.args[0]["fingerprint"] == ["asset-moderation", "e1"]
