"""Supervisor: turns a mixed Urdu / Roman Urdu / English sentence into structured actions."""
import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.normalize import clean_customer, clean_item, normalize_digits, normalize_unit
from app.agents.schemas import ParsedAction, ParsedIntent

log = logging.getLogger("dukaan.supervisor")

SYSTEM_PROMPT = """You are the order-taker for a small Pakistani kiryana shop. The shopkeeper talks to you in Urdu script, Roman Urdu, English, or a mix of all three in ONE sentence. Convert what they said into a list of actions.

ACTION TYPES and the words that signal them:
- sale: bika, bik gaya, bik gaye, bike, bikay, becha, bech diya, sold, بکا, بک گئے, بیچا
- restock: aaya, aa gaya, aaye, mangwaya, maal aaya, aya, received, آیا, آ گیا, منگوایا
- stock_out: khatam, khatam ho gaya, khatam hogaya, nahi raha, out of stock, ختم
- credit (customer takes goods on credit / udhaar): udhaar, udhar, likh do, khate mein likho, ادھار, لکھ دو
- payment (customer pays back): de gaya, de gayi, wapis kiye, jama, jama karwaye, paid, ادا, جمع, دے گیا
- stock_query: kitna bacha, kitna hai, kitne hain, stock kitna, کتنا بچا, کتنا ہے
- balance_query: kitna dena hai, kitna baqi hai, ka hisaab, کتنا دینا ہے
- unknown: anything that is not a shop action (greetings, chit-chat, unclear)

RULES:
1. One sentence can hold SEVERAL actions, separated by commas, "aur", "and", "or", "phir". Output one action per instruction, in the order spoken.
2. Numbers: always output digits. Urdu number words: ek=1, do=2, teen=3, char=4, paanch=5, chhe=6, saat=7, aath=8, nau=9, das=10, pandrah=15, bees=20, pachees=25, tees=30, chalees=40, pachas=50, saath=60, sattar=70, assi=80, nabbe=90, sau=100, dhai sau=250, paanch sau=500, hazaar/hazar=1000, dedh=1.5, dhai=2.5, aadha=0.5. "do sau"=200, "teen hazaar"=3000.
3. item: keep the item name EXACTLY as the shopkeeper said it (do NOT translate "chawal" to "rice", do NOT translate Urdu script to Roman), lowercase, without the unit and without the number.
4. unit: packet, kg, litre, dozen, bottle, piece, bag — or null if not said.
5. quantity is for goods (sale/restock). amount is rupees (credit/payment). "500 ka udhaar" means amount=500.
6. customer: the person's name only, without "ko", "ka", "se", "bhai", "sahab", "ne".
7. For stock_out, quantity is null. For queries, quantity and amount are null.
8. Never invent items, numbers or names that were not said. Fields that were not said are null.

EXAMPLES:
Input: 20 packet chawal bike, atta khatam, Ahmed ko 500 ka udhaar
Output: {"actions":[{"action":"sale","item":"chawal","quantity":20,"unit":"packet","customer":null,"amount":null},{"action":"stock_out","item":"atta","quantity":null,"unit":null,"customer":null,"amount":null},{"action":"credit","item":null,"quantity":null,"unit":null,"customer":"Ahmed","amount":500}]}

Input: Bilal bhai 1500 de gaye
Output: {"actions":[{"action":"payment","item":null,"quantity":null,"unit":null,"customer":"Bilal","amount":1500}]}

Input: پچاس کلو چینی آ گئی اور دال ختم ہو گئی
Output: {"actions":[{"action":"restock","item":"چینی","quantity":50,"unit":"kg","customer":null,"amount":null},{"action":"stock_out","item":"دال","quantity":null,"unit":null,"customer":null,"amount":null}]}

Input: cheeni kitni bachi hai aur Ahmed ne kitna dena hai
Output: {"actions":[{"action":"stock_query","item":"cheeni","quantity":null,"unit":null,"customer":null,"amount":null},{"action":"balance_query","item":null,"quantity":null,"unit":null,"customer":"Ahmed","amount":null}]}

Input: sold 3 bottles cooking oil, received bees packet doodh
Output: {"actions":[{"action":"sale","item":"cooking oil","quantity":3,"unit":"bottle","customer":null,"amount":null},{"action":"restock","item":"doodh","quantity":20,"unit":"packet","customer":null,"amount":null}]}

Input: Usman ke khate mein do sau likh do, 5 kilo ghee bika
Output: {"actions":[{"action":"credit","item":null,"quantity":null,"unit":null,"customer":"Usman","amount":200},{"action":"sale","item":"ghee","quantity":5,"unit":"kg","customer":null,"amount":null}]}
"""

SHORT_PROMPT = """Extract shop actions from the shopkeeper's message (Urdu/Roman Urdu/English).
Types: sale (bika/becha), restock (aaya/mangwaya), stock_out (khatam), credit (udhaar/likh do),
payment (de gaya/jama), stock_query (kitna bacha), balance_query (kitna dena hai), unknown.
Numbers as digits (bees=20, pachas=50, sau=100, hazaar=1000). Item names lowercase, untranslated.
amount = rupees for credit/payment. Unsaid fields are null."""


def _call_llm(system_prompt: str, text: str) -> ParsedIntent:
    llm = get_llm().with_structured_output(ParsedIntent, method="function_calling")
    result = llm.invoke([SystemMessage(system_prompt), HumanMessage(text)])
    if isinstance(result, dict):  # some providers hand back a dict
        result = ParsedIntent.model_validate(result)
    if not isinstance(result, ParsedIntent):
        raise ValueError(f"unparseable LLM output: {result!r}")
    return result


def _clean(intent: ParsedIntent) -> ParsedIntent:
    actions = []
    for a in intent.actions:
        actions.append(ParsedAction(
            action=a.action,
            item=clean_item(a.item),
            quantity=a.quantity,
            unit=normalize_unit(a.unit),
            customer=clean_customer(a.customer),
            amount=a.amount,
        ))
    return ParsedIntent(actions=actions or [ParsedAction(action="unknown")])


def _salvage(error: Exception) -> ParsedIntent | None:
    """Groq sometimes calls a tool named 'json' instead of ours; the JSON itself is fine — reuse it."""
    body = getattr(error, "body", None)
    if not isinstance(body, dict):
        return None
    gen = body.get("failed_generation") or (body.get("error") or {}).get("failed_generation")
    if not gen:
        return None
    try:
        data = json.loads(gen)
        args = data.get("arguments", data) if isinstance(data, dict) else data
        if isinstance(args, str):
            args = json.loads(args)
        return ParsedIntent.model_validate(args)
    except Exception:
        return None


def parse_intent(text: str) -> ParsedIntent:
    text = normalize_digits((text or "").strip())
    if not text:
        return ParsedIntent(actions=[ParsedAction(action="unknown")])
    for attempt, prompt in enumerate((SYSTEM_PROMPT, SHORT_PROMPT), start=1):
        try:
            return _clean(_call_llm(prompt, text))
        except Exception as e:  # network, schema, provider quirks
            salvaged = _salvage(e)
            if salvaged is not None:
                log.info("parse attempt %d: recovered output from provider error", attempt)
                return _clean(salvaged)
            log.warning("parse attempt %d failed: %s", attempt, e)
    return ParsedIntent(actions=[ParsedAction(action="unknown")])