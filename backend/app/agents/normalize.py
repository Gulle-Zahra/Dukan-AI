"""Small text/unit normalizers shared by the supervisor (no LLM, no DB)."""
import re

# Urdu/Persian (۰-۹) and Arabic-Indic (٠-٩) digits -> ASCII
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

_UNITS = {
    "packet": "packet", "packets": "packet", "pkt": "packet", "pkts": "packet",
    "packit": "packet", "paket": "packet", "پیکٹ": "packet",
    "kg": "kg", "kgs": "kg", "kilo": "kg", "kilos": "kg", "kilogram": "kg",
    "kilograms": "kg", "kelo": "kg", "کلو": "kg",
    "ltr": "litre", "ltrs": "litre", "litre": "litre", "litres": "litre",
    "liter": "litre", "liters": "litre", "l": "litre", "لیٹر": "litre",
    "dozen": "dozen", "darjan": "dozen", "درجن": "dozen",
    "bottle": "bottle", "bottles": "bottle", "botal": "bottle",
    "piece": "piece", "pieces": "piece", "pc": "piece", "pcs": "piece", "adad": "piece",
    "bag": "bag", "bags": "bag", "bori": "bag", "boriyan": "bag",
}


def normalize_digits(text: str) -> str:
    return text.translate(_DIGITS)


def normalize_unit(unit: str | None) -> str | None:
    if not unit:
        return None
    u = unit.strip().lower().rstrip(".")
    return _UNITS.get(u, u)


def clean_item(item: str | None) -> str | None:
    if not item:
        return None
    item = re.sub(r"\s+", " ", item).strip().lower()
    return item or None


def clean_customer(name: str | None) -> str | None:
    if not name:
        return None
    name = re.sub(r"\s+", " ", name).strip()
    # Roman names -> Title Case so "ahmed" and "Ahmed" hit the same khata
    return name.title() if name.isascii() else name


def fmt(n: float | None) -> str:
    """20.0 -> '20', 2.5 -> '2.5', 1500 -> '1,500'."""
    if n is None:
        return "?"
    return f"{n:,.0f}" if float(n).is_integer() else f"{n:,.2f}".rstrip("0").rstrip(".")
