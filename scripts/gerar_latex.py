import argparse
import json
from pathlib import Path
import sys
import re

from jinja2 import Environment, FileSystemLoader

# Adiciona o diretório raiz do projeto ao sys.path para importações
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from utils.cleaner import clean_title_for_output


def parse_dimension(value: str, default: float) -> float:
    """Extrai o valor numérico de uma string de dimensão (ex: '2.5cm' -> 2.5)."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.match(r"([0-9.]+)([a-zA-Z]+)", value.strip())
        if match:
            return float(match.group(1))
    return default


def gerar_latex(projeto: str, idioma_arg: str):
    base_dir = Path("projetos") / projeto
    config_path = base_dir / "config.json"
    
    templates_dir = base_dir / "templates" / "tex"
    estilos_config_path = base_dir / "estilos" / "estilo_livro.json" # Caminho para o JSON de estilos
    
    # --- Normalização do Idioma ---
    if idioma_arg.lower() == "pt_br":
        idioma_normalizado_para_path = "pt-BR"
        idioma_para_latex = "brazil"
    elif idioma_arg.lower() == "en":
        idioma_normalizado_para_path = "en-US"
        idioma_para_latex = "english"
    else:
        idioma_normalizado_para_path = idioma_arg
        idioma_para_latex = "english" 

    output_dir = base_dir / "output" / idioma_normalizado_para_path
    output_dir.mkdir(parents=True, exist_ok=True)
    output_tex_path = output_dir / "livro_completo.tex"

    if not config_path.exists():
        print(f"❌ Arquivo de configuração não encontrado: {config_path}")
        return

    if not templates_dir.exists():
        print(f"❌ Diretório de templates LaTeX não encontrado: {templates_dir}")
        print(f"Por favor, crie a pasta: {templates_dir}")
        return
    
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=False)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    titulo_livro = config.get("titulo", "Livro Digital")
    autor_livro = config.get("autor", "Autor Desconhecido")
    
    # --- Carrega e Pré-processa o JSON de estilos ---
    raw_styles_data = {}
    if estilos_config_path.exists():
        try:
            raw_styles_data = json.loads(estilos_config_path.read_text(encoding="utf-8"))
            print(f"✅ Estilos carregados de: {estilos_config_path}")
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao carregar estilos de {estilos_config_path}: {e}")
            print("Usando estilos padrão/fallback para continuar.")
    else:
        print(f"⚠️ Arquivo de estilos não encontrado em: {estilos_config_path}. Usando estilos padrão/fallback.")
    
    # Dicionário para armazenar os estilos já processados para o template
    processed_styles = {}

    # Estilos de Parágrafo Padrão
    p_def = raw_styles_data.get("paragraph_default", {})
    processed_styles["paragraph_default_font_size_pt"] = parse_dimension(p_def.get("font-size", "10pt"), 10.0)
    processed_styles["paragraph_default_text_indent_cm"] = parse_dimension(p_def.get("text-indent", "0.5cm"), 0.5)
    processed_styles["paragraph_default_line_height"] = float(p_def.get("line-height", "1.2"))
    processed_styles["paragraph_default_margin_bottom_cm"] = parse_dimension(p_def.get("margin-bottom", "0.2cm"), 0.2)
    processed_styles["paragraph_default_font_family"] = p_def.get("font-family", "Latin Modern Roman") # Fonte padrão para LaTeX
    processed_styles["paragraph_default_color_name"] = p_def.get("color", "text_gray") # Assumindo que a cor é um nome ou será definida

    # Estilos de Título Nível 1
    h1_def = raw_styles_data.get("heading_1", {})
    processed_styles["heading_1_font_size_pt"] = parse_dimension(h1_def.get("font-size", "24pt"), 24.0)
    processed_styles["heading_1_line_spacing_pt"] = round(processed_styles["heading_1_font_size_pt"] * 1.2, 2)
    processed_styles["heading_1_font_family"] = h1_def.get("font-family", "Latin Modern Sans") # Fonte padrão para LaTeX
    processed_styles["heading_1_color_name"] = h1_def.get("color", "DarkBlueHeading")
    processed_styles["heading_1_margin_top_cm"] = parse_dimension(h1_def.get("margin-top", "1cm"), 1.0)
    processed_styles["heading_1_margin_bottom_cm"] = parse_dimension(h1_def.get("margin-bottom", "0.5cm"), 0.5)

    # Margens do Documento
    processed_styles["document_margins_cm"] = parse_dimension(raw_styles_data.get("document_margins", "2.5cm"), 2.5)

    # Cores (passa o dicionário de cores cru, pois o template itera e processa o HEX)
    # Garante que as cores padrão estejam presentes, mesmo se não definidas no JSON
    default_colors = {
        "text_gray": "333333",
        "DarkBlueHeading": "000080"
    }
    # Atualiza default_colors com cores do JSON, se existirem e forem válidas (removendo '#' para o template)
    processed_colors = {}
    for name, hex_val in raw_styles_data.get("colors", {}).items():
        if isinstance(hex_val, str) and hex_val.startswith("#"):
            processed_colors[name] = hex_val[1:] # Remove o '#'
        else:
            processed_colors[name] = hex_val # Usa como está, se não for uma string com '#'
    
    # Combina as cores padrão com as cores processadas do arquivo, priorizando as do arquivo
    processed_styles["colors"] = {**default_colors, **processed_colors}


    # Carrega livro_estruturado.json
    livro_path = base_dir / "gerado_automaticamente" / idioma_normalizado_para_path / "livro_estruturado.json"
    if not livro_path.exists():
        print(f"❌ Arquivo livro_estruturado.json não encontrado: {livro_path}")
        return
    livro_data = json.loads(livro_path.read_text(encoding="utf-8"))

    # Criando a estrutura 'content' para o template LaTeX
    processed_content = {
        "title": titulo_livro,
        "author": autor_livro,
        "sections": []
    }
    
    parte_counter = 0
    capitulo_counter = 0

    for item in livro_data.get("conteudo", []):
        if item["tipo"] == "parte":
            parte_counter += 1
            processed_content["sections"].append({
                "type": "heading_part",
                "text": clean_title_for_output(item.get("titulo_parte", f"Parte {parte_counter}")),
                "content": []
            })
            for nested_chapter_item in item.get("capitulos", []):
                if nested_chapter_item["tipo"] == "capitulo":
                    capitulo_counter += 1
                    processed_content["sections"].append({
                        "type": "heading_1",
                        "text": clean_title_for_output(nested_chapter_item.get("titulo1", f"Capítulo {capitulo_counter}")),
                        "content": [{
                            "type": "paragraph_default",
                            "text": f"Este é um parágrafo de exemplo para o capítulo '{clean_title_for_output(nested_chapter_item.get('titulo1', f'Capítulo {capitulo_counter}'))}'."
                        }]
                    })
        elif item["tipo"] == "capitulo":
            capitulo_counter += 1
            # Se não houver partes, agrupa em "Capítulos Avulsos" ou trata individualmente
            # Este bloco pode precisar de refinamento dependendo de como você quer que capítulos avulsos apareçam no LaTeX
            # Para o template atual, estamos apenas adicionando como heading_1
            processed_content["sections"].append({
                "type": "heading_1",
                "text": clean_title_for_output(item.get("titulo1", f"Capítulo {capitulo_counter}")),
                "content": [{
                    "type": "paragraph_default",
                    "text": f"Este é um parágrafo de exemplo para o capítulo '{clean_title_for_output(item.get('titulo1', f'Capítulo {capitulo_counter}'))}'."
                }]
            })
    
    base_latex_tpl = env.get_template("base.tex.j2")
    latex_content = base_latex_tpl.render(
        styles=processed_styles,
        content=processed_content,
        lang=idioma_para_latex
    )

    with open(output_tex_path, "w", encoding="utf-8") as f:
        f.write(latex_content)

    print(f"✅ Arquivo LaTeX gerado com sucesso: {output_tex_path}")
    print(f"Para gerar o PDF, execute no terminal (após instalar LaTeX):")
    print(f"cd {output_dir}")
    print(f"pdflatex livro_completo.tex")


def main():
    parser = argparse.ArgumentParser(description="Gera a versão LaTeX de um projeto de livro.")
    parser.add_argument("--projeto", required=True, help="Nome do diretório do projeto (ex: liderando_transformacao)")
    parser.add_argument("--idioma", default="pt-BR", help="Idioma do livro (ex: pt-BR, en-US).")
    args = parser.parse_args()

    print(f"▶️ Iniciando etapa: Gerar LaTeX para o projeto '{args.projeto}' ({args.idioma})...")
    gerar_latex(args.projeto, args.idioma)
    print(f"✅ Etapa concluída: Gerar LaTeX")


if __name__ == "__main__":
    main()
