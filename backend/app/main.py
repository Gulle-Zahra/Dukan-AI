import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db.database import init_db
from app.db.seed import reset_and_seed
from app.api.routes import router
from app.agent_bridge import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Auto-seed if empty
    from app.db.database import SessionLocal
    from app.db.models import Product
    with SessionLocal() as db:
        if db.query(Product).count() == 0:
            reset_and_seed()
    start_scheduler()
    yield

app = FastAPI(lifespan=lifespan)

# This allows our React frontend to talk to our Python backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)