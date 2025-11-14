import json
import re
from typing import Optional, List, Dict


def text_to_price(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    s = re.sub(r"[^\d,\.]", "", s)
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None
