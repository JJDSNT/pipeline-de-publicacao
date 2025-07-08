#  utils/filters.py
from jinja2 import Environment


def pt_to_latex(value):
    # Garante que 'pt' esteja presente, mas remove para operar, depois adiciona
    if isinstance(value, str):
        return value.replace('pt', '') + 'pt'
    return f"{value}pt" # Se for um número, assume pt


def cm_to_latex(value):
    if isinstance(value, str):
        return value.replace('cm', '') + 'cm'
    return f"{value}cm"


def px_to_latex(value, base_dpi=96): # Exemplo para pixels para pt
    if isinstance(value, str) and value.endswith('px'):
        pixels = float(value.replace('px', ''))
        return f"{pixels * (72 / base_dpi)}pt"
    return value # Retorna o original se não for px


def hex_to_latex_color_name(hex_color_code):
    # Esta é uma função mais complexa. Pode ter um mapeamento pré-definido
    # ou gerar um nome único e a definição da cor.
    # Por simplicidade, vamos usar o formato HTML do xcolor aqui.
    if hex_color_code.startswith('#'):
        return f"custom{hex_color_code[1:]}"
    return hex_color_code # Retorna o original se não for hex


def get_latex_color_definitions(styles_json):
    # Esta função retornaria uma lista de \definecolor para todas as cores HEX no JSON
    color_definitions = []
    # Percorrer o JSON de estilos e extrair todas as cores HEX
    # Para cada cor, adicionar uma linha como '\definecolor{customRRGGBB}{HTML}{RRGGBB}'
    # Este seria um passo no seu script Python, antes de passar para o Jinja
    return color_definitions


def setup_jinja_env_with_filters(env):
    env.filters['pt_to_latex'] = pt_to_latex
    env.filters['cm_to_latex'] = cm_to_latex
    env.filters['px_to_latex'] = px_to_latex
    env.filters['hex_to_latex_color_name'] = hex_to_latex_color_name
    # Adicione mais filtros conforme necessário
    return env

# No seu script principal:
# env = Environment(loader=FileSystemLoader('.'))
# env = setup_jinja_env_with_filters(env)