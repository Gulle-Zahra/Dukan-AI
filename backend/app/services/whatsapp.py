import urllib.parse
import re

def build_wa_link(phone: str, text: str) -> str:
    # Normalize phone
    clean_phone = re.sub(r'[\+\s\-]', '', phone)
    if clean_phone.startswith('0'):
        clean_phone = '92' + clean_phone[1:]
    encoded_text = urllib.parse.quote(text)
    return f"https://wa.me/{clean_phone}?text={encoded_text}"