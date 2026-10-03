import re
from app.contracts import AgentResponse, ActionResult
from app.db import repo

# Ring buffer for activity (Phase H4)
activity_log = []

def log_activity(input_text: str, reply: str, status: str):
    activity_log.insert(0, {"input": input_text, "reply": reply, "status": status, "agents": "Supervisor -> Validator -> Mock"})
    if len(activity_log) > 10: activity_log.pop()

def run_agent(text: str, transcript: str | None = None) -> AgentResponse:
    actions = []
    reply = "Maine aapki baat samajh li."
    text_lower = text.lower()
    
    # 1. Atta Restock
    if "atta" in text_lower:
        p = repo.find_product("Atta")
        if p:
            repo.adjust_stock(p.id, 5, "restock", text)
            actions.append(ActionResult(type="restock", status="done", detail="Atta stock increased by 5."))
            reply = "Atta ka stock badha diya gaya hai."

    # 2. Daal Stock Check
    elif "daal" in text_lower and "stock" in text_lower:
        p = repo.find_product("Daal")
        if p:
            reply = f"Daal ka stock abhi {p.stock_qty} kg bacha hai."
            actions.append(ActionResult(type="info", status="done", detail="Checked Daal inventory."))
            
    # 3. DYNAMIC KHATA (Udhaar / Jama)
    else:
        # Find any number in the text
        numbers = re.findall(r'\d+', text_lower)
        amount = float(numbers[0]) if numbers else 0
        
        # Look for any of our seeded database customers
        customers = ["ahmed", "bilal", "sana", "rashid", "fatima", "usman"]
        found_customer = None
        for c in customers:
            if c in text_lower:
                found_customer = c.capitalize()
                break
                
        if found_customer and amount > 0:
            c_db = repo.find_or_create_customer(found_customer)
            if c_db:
                # If you say "diye" or "jama", it subtracts from their balance
                if any(w in text_lower for w in ["diye", "jama", "payment", "paid", "wapas"]):
                    repo.record_payment(c_db.id, amount, text)
                    actions.append(ActionResult(type="payment", status="done", detail=f"Recorded Rs {amount} payment from {found_customer}."))
                    reply = f"{found_customer} ka {amount} jama kar liya gaya hai. Khata update ho gaya."
                
                # If you say "udhaar" or "liye", it adds to their balance
                elif any(w in text_lower for w in ["udhaar", "liye", "khata"]):
                    repo.add_credit(c_db.id, amount, text)
                    actions.append(ActionResult(type="credit", status="done", detail=f"Added Rs {amount} credit to {found_customer}."))
                    reply = f"{found_customer} ke khate mein {amount} ka udhaar likh liya hai."

    res = AgentResponse(input_text=text, transcript=transcript, actions=actions, reply_text=reply, pending_message_ids=[])
    log_activity(text, reply, "success")
    return res

def transcribe(audio_bytes: bytes, filename: str) -> str:
    return "Yeh ek mock transcript hai: 5 kilo atta aya."

def run_sweep() -> list[int]:
    created = []
    customers = repo.get_overdue_customers(min_balance=100, days=5)
    for c in customers:
        if not repo.has_pending_message("payment_reminder", c.id):
            msg = repo.create_pending_message("payment_reminder", c.name, c.phone, f"Assalam o Alaikum {c.name}, aap ka udhaar {c.balance} PKR baqi hai.", "scheduler", c.id)
            created.append(msg.id)
    return created

def start_scheduler() -> None:
    pass