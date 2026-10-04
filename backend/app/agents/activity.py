"""Live activity feed for the Overview tab (same shape as mock_agent.activity_log)."""
from threading import Lock

activity_log: list[dict] = []
_lock = Lock()
MAX_ITEMS = 10


def record(input_text: str, reply: str, status: str, agents: str) -> None:
    with _lock:
        activity_log.insert(0, {"input": input_text, "reply": reply, "status": status, "agents": agents})
        del activity_log[MAX_ITEMS:]  # in place, so the list imported elsewhere stays the same object