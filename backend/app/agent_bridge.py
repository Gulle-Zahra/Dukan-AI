import os
from dotenv import load_dotenv

load_dotenv()

USE_MOCK = os.getenv("USE_MOCK_AGENT", "true").lower() == "true"

if USE_MOCK:
    from app.mock_agent import run_agent, transcribe, run_sweep, start_scheduler, activity_log
else:
    # Assuming Zahra creates these exact modules and signatures
    from app.agents.graph import run_agent
    from app.speech.stt import transcribe
    from app.scheduler.jobs import run_sweep, start_scheduler
    activity_log = [] # Replace with Zahra's logic if needed later