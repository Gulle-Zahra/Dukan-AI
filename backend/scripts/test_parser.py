"""Parser smoke test.

  python scripts/test_parser.py           # print parsed JSON for 12 sentences
  python scripts/test_parser.py --check   # pass/fail table vs expected action types
  python scripts/test_parser.py --audio   # transcribe every file in samples/ then parse
"""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from app.agents.supervisor import parse_intent  # noqa: E402

CASES = [
    ("20 packet chawal bike, atta khatam, Ahmed ko 500 ka udhaar", ["sale", "stock_out", "credit"]),
    ("Ahmed 200 de gaya", ["payment"]),
    ("bees kilo cheeni aa gayi", ["restock"]),
    ("daal khatam ho gayi", ["stock_out"]),
    ("chawal kitna bacha hai?", ["stock_query"]),
    ("Bilal ne kitna dena hai", ["balance_query"]),
    ("پچاس کلو آٹا آ گیا", ["restock"]),
    ("۲۰ پیکٹ چاول بک گئے اور گھی ختم", ["sale", "stock_out"]),
    ("احمد کو پانچ سو ادھار لکھ دو", ["credit"]),
    ("sold 5 kg sugar and received 10 litre cooking oil", ["sale", "restock"]),
    ("Usman bhai ke khate mein hazaar likh do, phir 3 pkt doodh becha", ["credit", "sale"]),
    ("assalam o alaikum, kya haal hai", ["unknown"]),
]


def show_json():
    for text, _ in CASES:
        print(f"\n> {text}")
        print(parse_intent(text).model_dump_json(indent=2, exclude_none=True))


def check():
    passed = 0
    print(f"{'#':>2}  {'RESULT':6}  {'EXPECTED':28}  {'GOT':28}  INPUT")
    for i, (text, expected) in enumerate(CASES, 1):
        got = [a.action for a in parse_intent(text).actions]
        ok = got == expected
        passed += ok
        print(f"{i:>2}  {'PASS' if ok else 'FAIL':6}  {','.join(expected):28}  {','.join(got):28}  {text}")
    print(f"\n{passed}/{len(CASES)} passed")
    return passed == len(CASES)


def audio():
    from app.speech.stt import ALLOWED_EXT, transcribe
    files = sorted(p for p in (BACKEND / "samples").glob("*") if p.suffix.lower() in ALLOWED_EXT)
    if not files:
        print("No audio files in backend/samples/")
        return
    for f in files:
        text = transcribe(f.read_bytes(), f.name)
        print(f"\n[{f.name}] transcript: {text}")
        print(parse_intent(text).model_dump_json(indent=2, exclude_none=True))


if __name__ == "__main__":
    if "--audio" in sys.argv:
        audio()
    elif "--check" in sys.argv:
        sys.exit(0 if check() else 1)
    else:
        show_json()
