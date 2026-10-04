"""End-to-end demo rehearsal: reset DB, run the exact demo script, print PASS/FAIL.

  python scripts/demo_check.py
Needs a working LLM in .env. Seed must contain: chawal (>=20 in stock), atta (with a supplier
that has a phone), cheeni (< 2000 in stock), and customer Ahmed with a phone.
"""
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
os.environ["DEMO_MODE"] = "true"  # reminders appear immediately
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")

from app.agents.graph import run_agent  # noqa: E402
from app.agents.repo_provider import USE_FAKE_REPO, repo  # noqa: E402
from app.scheduler.jobs import run_sweep  # noqa: E402

report: list[tuple[str, bool, str]] = []


def check(name: str, ok: bool, info: str = "") -> bool:
    report.append((name, bool(ok), info))
    return ok


def reset_db() -> None:
    if USE_FAKE_REPO:
        from app.agents import _fake_repo
        _fake_repo.reset()
        return
    from app.db import seed
    for fn in ("reset_and_seed", "reset_db", "seed", "run", "main"):
        if callable(getattr(seed, fn, None)):
            getattr(seed, fn)()
            return
    raise RuntimeError("db/seed.py has no reset_and_seed()/reset_db()/seed()/main() function")


def main() -> int:
    try:
        reset_db()
        check("0. Reset DB", True, "fake repo" if USE_FAKE_REPO else "db/seed.py")
    except Exception as e:
        check("0. Reset DB", False, repr(e))
        return finish()

    # 1. Multi-action sentence + auto reorder
    atta = repo.find_product("atta")
    r = run_agent("20 packet chawal bike, atta khatam, Ahmed ko 500 ka udhaar")
    done = [a for a in r.actions if a.status == "done"]
    check("1a. 3 actions done", len(r.actions) == 3 and len(done) == 3,
          " | ".join(f"{a.type}:{a.status}" for a in r.actions))
    check("1b. Supplier order pending for atta",
          atta is not None and repo.has_pending_message("supplier_order", atta.id),
          f"pending ids {r.pending_message_ids}")

    # 2. Payment reduces balance
    before = repo.find_or_create_customer("Ahmed").balance
    r = run_agent("Ahmed 200 de gaya")
    after = repo.find_or_create_customer("Ahmed").balance
    check("2. Ahmed balance -200", abs((before - after) - 200) < 0.01,
          f"Rs {before:g} -> Rs {after:g} | {r.reply_text}")

    # 3. Over-sale is rejected
    r = run_agent("2000 packet cheeni bik gayi")
    check("3. Over-sale rejected",
          len(r.actions) == 1 and r.actions[0].status == "rejected" and r.actions[0].type == "sale",
          r.reply_text)

    # 4. Scheduler drafts a payment reminder
    new_ids = run_sweep()
    ahmed = repo.find_or_create_customer("Ahmed")
    check("4. Payment reminder pending", repo.has_pending_message("payment_reminder", ahmed.id),
          f"sweep created {new_ids}")
    return finish()


def finish() -> int:
    print("\n" + "=" * 72 + "\nDUKAAN AI — DEMO CHECK\n" + "=" * 72)
    for name, ok, info in report:
        print(f"{'PASS' if ok else 'FAIL'}  {name}")
        if info:
            print(f"      {info}")
    passed = sum(ok for _, ok, _ in report)
    verdict = "ALL GOOD — demo ready" if passed == len(report) else "NOT READY"
    print("=" * 72 + f"\n{passed}/{len(report)} passed — {verdict}")
    return 0 if passed == len(report) else 1


if __name__ == "__main__":
    sys.exit(main())
