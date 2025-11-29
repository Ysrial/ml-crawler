import json
import re
from typing import Optional, List, Dict


def text_to_price(s: Optional[str]) -> Optional[float]:
    """
    Converte string de preço para float, tratando formatos brasileiros.
    Exemplos: "249,90" → 249.90 | "1.249,50" → 1249.50 | "249.90" → 249.90
    """
    if not s:
        return None
    
    # Remover espaços em branco
    s = s.strip()
    
    # Remover tudo que não seja dígito, vírgula ou ponto
    s = re.sub(r"[^\d,\.]", "", s)
    
    if not s:
        return None
    
    # Detectar formato: vírgula é sempre separador decimal em português
    # Se houver múltiplos separadores, o último é decimal
    if "," in s and "." in s:
        # Formato: 1.234,56 → remove ponto (separador de milhares), substitui vírgula
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        # Formato: 249,90 → substitui vírgula por ponto
        s = s.replace(",", ".")
    # Se só tem ponto, pode ser 249.90 ou 249 (sem decimais)
    # Deixa como está
    
    try:
        valor = float(s)
        # Evitar valores absurdos (< 0.01 ou > 1.000.000)
        if valor < 0.01 or valor > 1000000:
            return None
        return round(valor, 2)
    except (ValueError, TypeError):
        return None
