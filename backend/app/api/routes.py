from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from typing import List
from app.db import repo, models
from app.db.database import SessionLocal
from app.agent_bridge import run_agent, transcribe, run_sweep, activity_log
from app.services.whatsapp import build_wa_link
from app.db.seed import reset_and_seed

router = APIRouter(prefix="/api")

class ChatRequest(BaseModel):
    text: str

@router.post("/chat")
def chat(req: ChatRequest):
    return run_agent(req.text)

@router.post("/voice")
async def voice(audio: UploadFile = File(...)):
    bytes_data = await audio.read()
    transcript = transcribe(bytes_data, audio.filename)
    return run_agent(transcript, transcript=transcript)

@router.get("/products")
def get_products():
    return repo.list_products()

@router.get("/customers")
def get_customers():
    with SessionLocal() as db:
        return db.query(models.Customer).order_by(models.Customer.balance.desc()).all()

@router.get("/transactions")
def get_transactions(limit: int = 20):
    with SessionLocal() as db:
        return db.query(models.Transaction).order_by(models.Transaction.created_at.desc()).limit(limit).all()

@router.get("/approvals")
def get_approvals(status: str = "pending"):
    with SessionLocal() as db:
        return db.query(models.PendingMessage).filter_by(status=status).order_by(models.PendingMessage.created_at.desc()).all()

@router.post("/approvals/{id}/approve")
def approve_message(id: int):
    with SessionLocal() as db:
        msg = db.query(models.PendingMessage).get(id)
        msg.status = "approved"
        db.commit()
        link = build_wa_link(msg.phone, msg.message_text)
        return {"wa_link": link, "message": "Approved"}

class EditMsgRequest(BaseModel):
    message_text: str

@router.post("/approvals/{id}/edit")
def edit_message(id: int, req: EditMsgRequest):
    with SessionLocal() as db:
        msg = db.query(models.PendingMessage).get(id)
        msg.message_text = req.message_text
        db.commit()
        db.refresh(msg)
        return msg

@router.post("/approvals/{id}/reject")
def reject_message(id: int):
    with SessionLocal() as db:
        msg = db.query(models.PendingMessage).get(id)
        msg.status = "rejected"
        db.commit()
        return {"message": "Rejected"}

@router.post("/sweep")
def trigger_sweep():
    ids = run_sweep()
    return {"created_ids": ids}

@router.post("/reset")
def reset_db():
    reset_and_seed()
    return {"status": "success"}

@router.get("/stats")
def get_stats():
    prods = repo.list_products()
    low_stock = repo.get_low_stock()
    with SessionLocal() as db:
        # FIXED: Only sum balances that are greater than 0
        total_udhaar = sum([c.balance for c in db.query(models.Customer).filter(models.Customer.balance > 0).all()])
        pending = db.query(models.PendingMessage).filter_by(status="pending").count()
    return {
        "total_products": len(prods),
        "low_stock_count": len(low_stock),
        "total_udhaar": total_udhaar,
        "pending_approvals": pending
    }

@router.get("/activity")
def get_activity():
    return activity_log