"""Proactive sweeps: low-stock reorders and overdue-payment reminders (all need approval)."""
import logging
import os
import threading

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

from app.agents import reorder_agent
from app.agents.activity import record
from app.agents.normalize import fmt
from app.agents.repo_provider import repo

load_dotenv()
log = logging.getLogger("dukaan.scheduler")

_scheduler: BackgroundScheduler | None = None
_start_lock = threading.Lock()
_sweep_lock = threading.Lock()


def _flag(name: str) -> bool:
    return os.getenv(name, "false").strip().lower() in ("1", "true", "yes")


def reminder_text(name: str, balance: float) -> str:
    return (f"Assalam o Alaikum {name} bhai, aap ka Rs {fmt(balance)} baqi hai. "
            f"Jab mauqa mile ada kar dein. Shukriya.")


def _low_stock_sweep() -> list[int]:
    ids = [p.id for p in repo.get_low_stock()]
    return reorder_agent.check_and_draft(ids, source="scheduler")


def _overdue_sweep() -> list[int]:
    min_balance = float(os.getenv("OVERDUE_MIN_BALANCE", "500"))
    days = 0 if _flag("DEMO_MODE") else int(os.getenv("OVERDUE_DAYS", "7"))
    new_ids = []
    for c in repo.get_overdue_customers(min_balance, days):
        try:
            if not c.phone or repo.has_pending_message("payment_reminder", c.id):
                continue
            msg = repo.create_pending_message(
                kind="payment_reminder", recipient_name=c.name, phone=c.phone,
                message_text=reminder_text(c.name, c.balance), source="scheduler", ref_id=c.id,
            )
            new_ids.append(msg.id)
            log.info("Drafted payment_reminder #%s for %s (Rs %s)", msg.id, c.name, fmt(c.balance))
        except Exception:
            log.exception("Reminder draft failed for customer %s", c.id)
    return new_ids


def run_sweep() -> list[int]:
    if not _sweep_lock.acquire(blocking=False):  # manual trigger + timer at the same moment
        log.info("Sweep already running, skipping")
        return []
    try:
        new_ids = []
        for name, sweep in (("low_stock", _low_stock_sweep), ("overdue", _overdue_sweep)):
            try:
                new_ids += sweep()
            except Exception:
                log.exception("%s sweep failed", name)
        log.info("Sweep done: %d new pending message(s) %s", len(new_ids), new_ids)
        if new_ids:  # only log sweeps that did something, so the feed isn't flooded
            record("⏰ Scheduler sweep", f"📦 {len(new_ids)} naye message approval ke liye tayyar",
                   "done", "Scheduler -> Reorder / Reminder")
        return new_ids
    finally:
        _sweep_lock.release()


def start_scheduler() -> None:
    global _scheduler
    with _start_lock:
        if _scheduler is not None and _scheduler.running:
            log.info("Scheduler already running")
            return
        interval = int(os.getenv("SWEEP_INTERVAL_SECONDS", "120"))
        _scheduler = BackgroundScheduler(daemon=True)
        _scheduler.add_job(run_sweep, "interval", seconds=interval, id="dukaan_sweep",
                           replace_existing=True, max_instances=1, coalesce=True)
        _scheduler.start()
        log.info("Scheduler started: sweep every %ss (DEMO_MODE=%s)", interval, _flag("DEMO_MODE"))


def stop_scheduler() -> None:
    global _scheduler
    with _start_lock:
        if _scheduler is not None and _scheduler.running:
            _scheduler.shutdown(wait=False)
        _scheduler = None