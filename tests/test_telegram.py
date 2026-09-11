"""Telegram transport — thin, and unable to take the process down."""
from __future__ import annotations

from trading_agent.telegram_bot import Telegram


def ok(result):
    return lambda url, data: {"ok": True, "result": result}


def boom(url, data):
    raise OSError("network down")


def test_send_returns_false_rather_than_raising():
    """A missed notification is an inconvenience; an aborted cycle leaves a
    position unmanaged."""
    assert Telegram("t", "1", opener=boom).send("hi") is False


def test_polling_failure_yields_nothing_rather_than_raising():
    assert Telegram("t", "1", opener=boom).updates() == []


def test_only_the_owner_can_drive_the_bot():
    """The token is a bearer credential — anyone who finds the bot can message
    it. Messages from other chats must be ignored entirely."""
    updates = [
        {"update_id": 1, "message": {"chat": {"id": 999}, "text": "/stop"}},
        {"update_id": 2, "message": {"chat": {"id": 1}, "text": "/status"}},
    ]
    texts, offset = Telegram("t", "1", opener=ok(updates)).messages_from_owner()
    assert texts == ["/status"], "a stranger's /stop must not be honoured"
    assert offset == 3


def test_offset_advances_past_ignored_messages():
    """Otherwise a stranger's message is re-fetched forever."""
    updates = [{"update_id": 7, "message": {"chat": {"id": 999}, "text": "x"}}]
    _, offset = Telegram("t", "1", opener=ok(updates)).messages_from_owner()
    assert offset == 8


def test_long_messages_are_truncated_not_dropped():
    sent = {}

    def capture(url, data):
        sent["data"] = data
        return {"ok": True}

    Telegram("t", "1", opener=capture).send("x" * 9000)
    assert sent["data"] is not None
    assert len(sent["data"]) < 9000, "must respect Telegram's 4096 limit"
