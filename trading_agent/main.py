"""Entrypoint.

Two loops, deliberately not one:

  * the **command loop** runs in the main thread and polls Telegram every few
    seconds. It is the only thing that must never be slow.
  * the **work loop** runs in a daemon thread and does everything expensive —
    reconciliation, catalysts, research, the trading cycle.

That split is ACCEPTANCE B4. A wedged model call blocks the work loop; it must
not block /stop. Each loop opens its own SQLite handle on the same file —
sqlite3 refuses a connection shared across threads, and WAL makes independent
handles safe — so the command loop can halt trading while the work loop is
stuck inside a network call it cannot interrupt.
"""
from __future__ import annotations

import datetime as dt
import logging
import signal
import threading
import time

from trading_agent.agent import run_cycle
from trading_agent.audit import AuditLog, new_correlation_id
from trading_agent.broker import Broker
from trading_agent.catalysts import CatalystFeed
from trading_agent.commands import handle_command
from trading_agent.config import Config
from trading_agent.reasoning import ReasoningClient
from trading_agent.state import State
from trading_agent.telegram_bot import Telegram
from trading_agent.universe import Universe
from trading_agent.views import ViewStore

log = logging.getLogger("trading_agent")

COMMAND_POLL_SECONDS = 3
CYCLE_INTERVAL_SECONDS = 900  # 15 minutes; catalysts do not move by the second

_stop = threading.Event()


def _install_signal_handlers() -> None:
    def handler(signum, _frame):
        # systemd sends SIGTERM on stop and on restart. Exiting cleanly means
        # in-flight SQLite writes finish rather than being torn off.
        log.info("signal %s received, shutting down", signum)
        _stop.set()

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)


def work_loop(config: Config, paths: dict) -> None:
    """Everything expensive. Its own state handle; never touches the main one."""
    state = State(paths["state_db"])
    views = ViewStore(paths["views_db"])
    audit = AuditLog(paths["audit_log"])
    universe = Universe(paths["universe_cache"])
    broker = Broker.from_config(config)
    reasoner = ReasoningClient.from_config(config)
    feed = CatalystFeed(universe)

    # Reconcile once before anything else. Starting a trading process on an
    # unverified picture of the account is the one thing worth refusing to do.
    cid = new_correlation_id()
    try:
        audit.record("startup_reconcile", cid, broker.reconcile(state))
    except Exception as exc:  # noqa: BLE001
        audit.record("startup_reconcile_failed", cid, {"error": str(exc)})
        log.error("startup reconciliation failed: %s", exc)

    while not _stop.is_set():
        try:
            result = run_cycle(
                state=state, config=config, broker=broker, feed=feed,
                reasoner=reasoner, audit=audit, views=views,
                now=dt.datetime.now(dt.timezone.utc),
            )
            log.info("cycle: ran=%s submitted=%s skipped=%s",
                     result.ran, result.submitted, result.skipped_reason)
        except Exception as exc:  # noqa: BLE001
            # A cycle that throws must not kill the process: the kill switch
            # and the command loop still need to be answering.
            log.exception("cycle failed: %s", exc)
            audit.record("cycle_failed", new_correlation_id(), {"error": str(exc)})
        _stop.wait(CYCLE_INTERVAL_SECONDS)


def command_loop(config: Config, paths: dict) -> None:
    """Telegram commands. Kept trivial so it is always responsive."""
    state = State(paths["state_db"])
    tg = Telegram(config.telegram_bot_token, config.telegram_chat_id)
    offset = 0
    while not _stop.is_set():
        texts, offset = tg.messages_from_owner(offset)
        for text in texts:
            result = handle_command(text, state=state)
            if result.text:
                tg.send(result.text)
            if result.changed:
                log.warning("operator command applied: %s", text.split()[0])
        _stop.wait(COMMAND_POLL_SECONDS)


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    _install_signal_handlers()

    config = Config.from_env()
    import os

    root = os.environ.get("TRADING_AGENT_ROOT", "/opt/trading-agent")
    paths = {
        "state_db": os.environ.get("STATE_DB", f"{root}/state.db"),
        "views_db": f"{root}/views.db",
        "audit_log": f"{os.environ.get('LOG_DIR', root + '/logs')}/audit.log",
        "universe_cache": f"{root}/universe.json",
    }

    log.info("starting: endpoint=%s live=%s", config.endpoint, config.is_live)
    if config.is_live:
        # Loud on purpose. This line in the journal is the last cheap warning
        # before real money is involved.
        log.warning("LIVE TRADING ENABLED — real money is at risk")

    worker = threading.Thread(target=work_loop, args=(config, paths), daemon=True)
    worker.start()
    try:
        command_loop(config, paths)
    finally:
        _stop.set()
        worker.join(timeout=10)
    log.info("stopped")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
