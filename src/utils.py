import json
import re
from typing import Optional, List, Dict


def text_to_price(s: Optional[str]) -> Optional[float]:
    if not s:
        return None
    
    s = re.sub(r"[^\d,\.]", "", s).strip()
    
    if not s:
        return None
    
    dot_count = s.count('.')
    comma_count = s.count(',')
    
    if comma_count == 1 and dot_count == 0:
        s = s.replace(",", ".")
    
    elif dot_count == 1 and comma_count == 0:
        parts = s.split('.')
        if len(parts) == 2:
            before, after = parts
            if len(after) == 2 and len(before) <= 3:
                pass
            elif len(after) == 3:
                s = s.replace(".", "")
            elif len(after) == 2 and len(before) > 3:
                pass
            elif len(after) == 2 and len(before) > 3:
                pass
            else:
                s = s.replace(".", "")
    
    elif dot_count >= 1 and comma_count >= 1:
        last_dot_pos = s.rfind('.')
        last_comma_pos = s.rfind(',')
        
        if last_comma_pos > last_dot_pos:
            parts = s.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(".", "").replace(",", ".")
        
        else:
            parts = s.split('.')
            if len(parts) == 2 and len(parts[1]) <= 2:
                s = s.replace(",", "")
            else:
                s = s.replace(",", "")
    
    elif dot_count > 1 and comma_count == 0:
        s = s.replace(".", "")
    elif comma_count > 1 and dot_count == 0:
        s = s.replace(",", "")
    
    try:
        return float(s)
    except ValueError:
        return None
