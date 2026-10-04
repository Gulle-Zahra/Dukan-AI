"""Run the full agent graph on 8 sentences.  python scripts/test_graph.py"""
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from app.agents.graph import run_agent  # noqa: E402

SENTENCES = [
    "20 packet chawal bike, atta khatam, Ahmed ko 500 ka udhaar",
    "Ahmed 200 de gaya",
    "2000 packet cheeni bik gayi",
    "bees kilo cheeni aa gayi",
    "chawal kitna bacha hai aur Ahmed ne kitna dena hai",
    "5 packet chaawal bike",
    "۲۰ پیکٹ چاول بک گئے",
    "kya haal hai bhai",
]

if __name__ == "__main__":
    for s in SENTENCES:
        r = run_agent(s)
        print("\n" + "=" * 70 + f"\n> {s}\n" + r.reply_text)
        print(r.model_dump_json(indent=2))
