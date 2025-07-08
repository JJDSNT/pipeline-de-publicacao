import re
from typing import List, Dict
from utils.cleaner import clean_title_for_output # Já importado na modificação anterior

# Mapeamento de numerais romanos para inteiros
_ROMAN_MAP = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}

def _roman_to_int(s: str) -> int:
    """Converte um numeral romano (I, V, X, L, C, D, M) para inteiro."""
    result = 0
    i = 0
    while i < len(s):
        if i + 1 < len(s) and _ROMAN_MAP.get(s[i], 0) < _ROMAN_MAP.get(s[i+1], 0):
            result += _ROMAN_MAP[s[i+1]] - _ROMAN_MAP[s[i]]
            i += 2
        else:
            result += _ROMAN_MAP.get(s[i], 0) # Use .get() para evitar KeyError em caracteres inválidos
            i += 1
    return result

def extrair_numero_identificador(nome: str) -> int:
    """
    Extrai o número inteiro ou romano de uma string de título (capítulo ou parte).
    Usado para ordenação numérica.
    Ex: '# Capítulo 1 --- Prólogo' -> 1
    Ex: '# Parte I -- Fundamentos' -> 1
    Ex: '8.2 Liderança Ágil' -> 8
    """
    # Tenta extrair o número de "Capítulo X"
    match_cap = re.match(r"(?:#\s*)?Capítulo\s*(\d+)", nome, re.IGNORECASE)
    if match_cap:
        return int(match_cap.group(1))
    
    # Tenta extrair o número de "Parte X" (romano)
    match_parte = re.match(r"(?:#\s*)?Parte\s*([IVXLCDM]+)", nome, re.IGNORECASE)
    if match_parte:
        # Adição de verificação defensiva para garantir que o grupo 1 exista
        # (Embora teoricamente deva existir se a regex match_parte correspondeu)
        if len(match_parte.groups()) > 0: # Verifica se há pelo menos um grupo de captura
            roman_num_str = match_parte.group(1)
            # Adição de verificação para garantir que a string capturada não seja vazia
            if roman_num_str:
                return _roman_to_int(roman_num_str)
        # Se o grupo não for capturado ou for vazio, a função continua para as próximas tentativas
        
    # Tenta extrair o número de uma string que começa com número (ex: "1.2 ...")
    match_num = re.match(r"^(\d+)", nome)
    if match_num:
        return int(match_num.group(1))
        
    return float("inf") # Para itens sem número, para que fiquem no final

def gerar_ordem(config: Dict, titulos_disponiveis: List[str]) -> List[str]:
    """
    Gera uma lista ordenada de títulos de partes e capítulos com base no config.json.
    `titulos_disponiveis` deve conter os títulos exatos (ex: "# Capítulo 1 ...', '# Parte I ...').
    O retorno serão os títulos LIMPOS (sem '# ' e com travessão).
    """
    ordem_predefinida = config.get("ordem_predefinida", [])
    mapeamento_partes_config = {
        int(k): int(v) for k, v in config.get("mapeamento_partes", {}).items()
    }

    titulos_limpos_para_originais = {}
    titulos_originais_por_tipo = {
        "capitulo": [],
        "parte": [],
        "componente": []
    }

    for titulo in titulos_disponiveis:
        titulo_limpo = clean_title_for_output(titulo)
        titulos_limpos_para_originais[titulo_limpo] = titulo

        if re.match(r"(?:#\s*)?Capítulo\s*\d+", titulo, re.IGNORECASE):
            titulos_originais_por_tipo["capitulo"].append(titulo)
        elif re.match(r"(?:#\s*)?Parte\s*[IVXLCDM]+", titulo, re.IGNORECASE):
            titulos_originais_por_tipo["parte"].append(titulo)
        else:
            titulos_originais_por_tipo["componente"].append(titulo)

    capitulos_ordenados = sorted(
        titulos_originais_por_tipo["capitulo"],
        key=extrair_numero_identificador
    )

    ordem_final = []
    parte_adicionada_ultima = None

    for item_predefinido in ordem_predefinida:
        if item_predefinido == "PARTES":
            for cap_titulo_original in capitulos_ordenados:
                numero_capitulo = extrair_numero_identificador(cap_titulo_original)
                
                titulo_da_parte_para_adicionar = None
                for num_parte_int, cap_inicio_parte in mapeamento_partes_config.items():
                    if numero_capitulo == cap_inicio_parte:
                        for parte_titulo_original in titulos_originais_por_tipo["parte"]:
                            if extrair_numero_identificador(parte_titulo_original) == num_parte_int:
                                titulo_da_parte_para_adicionar = parte_titulo_original
                                break
                        break
                
                if titulo_da_parte_para_adicionar and titulo_da_parte_para_adicionar != parte_adicionada_ultima:
                    ordem_final.append(clean_title_for_output(titulo_da_parte_para_adicionar))
                    parte_adicionada_ultima = titulo_da_parte_para_adicionar
                
                ordem_final.append(clean_title_for_output(cap_titulo_original))
        else:
            ordem_final.append(clean_title_for_output(item_predefinido))

    return ordem_final
