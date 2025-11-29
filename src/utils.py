import json
import re
from typing import Optional, List, Dict


def text_to_price(s: Optional[str]) -> Optional[float]:
    """
    Converte string de preço para float, detectando automaticamente o formato.
    Suporta formatos:
    - Brasileiro: 1.234,56 (ponto = milhares, vírgula = decimal)
    - Americano: 1,234.56 (vírgula = milhares, ponto = decimal)
    - Simples: 249.90 ou 249,90 (detecta automaticamente)
    """
    if not s:
        return None
    
    # Remove espaços e caracteres não numéricos (exceto . e ,)
    s = re.sub(r"[^\d,\.]", "", s).strip()
    
    if not s:
        return None
    
    # Contar pontos e vírgulas
    dot_count = s.count('.')
    comma_count = s.count(',')
    
    # Caso 1: Apenas vírgula (formato brasileiro simples: 249,90)
    if comma_count == 1 and dot_count == 0:
        s = s.replace(",", ".")
    
    # Caso 2: Apenas ponto
    elif dot_count == 1 and comma_count == 0:
        # Verificar se é decimal ou separador de milhares
        parts = s.split('.')
        if len(parts) == 2:
            before, after = parts
            # Se tem exatamente 2 dígitos depois do ponto e 1-3 antes, é decimal
            # Exemplos: 9.99, 49.90, 249.90
            if len(after) == 2 and len(before) <= 3:
                # É decimal, mantém o ponto
                pass
            # Se tem 3 dígitos depois, é separador de milhares
            # Exemplos: 4.798 -> 4798
            elif len(after) == 3:
                s = s.replace(".", "")
            # Se tem 2 dígitos depois mas mais de 3 antes, pode ser decimal sem separador de milhares
            # Exemplos: 1999.99 -> 1999.99 (não 199999!)
            elif len(after) == 2 and len(before) > 3:
                # É decimal, mantém o ponto
                pass
            # Outros casos: remover ponto
            else:
                s = s.replace(".", "")
    
    # Caso 3 e 4: Ambos pontos e vírgulas presentes
    # Precisamos verificar qual separador vem por último para determinar o formato
    elif dot_count >= 1 and comma_count >= 1:
        last_dot_pos = s.rfind('.')
        last_comma_pos = s.rfind(',')
        
        # Se a vírgula vem depois do ponto = formato brasileiro (1.234,56)
        if last_comma_pos > last_dot_pos:
            # Verificar quantos dígitos tem depois da vírgula
            parts = s.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Vírgula é decimal (1-2 dígitos depois)
                s = s.replace(".", "").replace(",", ".")
            else:
                # Caso estranho, tratar como brasileiro mesmo assim
                s = s.replace(".", "").replace(",", ".")
        
        # Se o ponto vem depois da vírgula = formato americano (1,234.56)
        else:
            # Verificar quantos dígitos tem depois do ponto
            parts = s.split('.')
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Ponto é decimal (1-2 dígitos depois)
                s = s.replace(",", "")
            else:
                # Caso estranho, remover vírgulas
                s = s.replace(",", "")
    
    # Caso 5: Múltiplos separadores do mesmo tipo (remover todos)
    elif dot_count > 1 and comma_count == 0:
        s = s.replace(".", "")
    elif comma_count > 1 and dot_count == 0:
        s = s.replace(",", "")
    
    try:
        return float(s)
    except ValueError:
        return None
