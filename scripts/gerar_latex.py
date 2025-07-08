# scripts/gerar_latex.py
import argparse
import json
from pathlib import Path
import sys
import re
import subprocess
import time # Adicionado para logs de tempo

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

def convert_markdown_to_latex(markdown_text: str) -> str:
    """Converte um bloco de texto Markdown para LaTeX usando Pandoc."""
    if not markdown_text:
        return ""
    try:
        result = subprocess.run(
            ['pandoc', '-f', 'markdown', '-t', 'latex', '--wrap=none', '--no-highlight'],
            input=markdown_text.encode('utf-8'),
            capture_output=True,
            check=True
        )
        latex_output = result.stdout.decode('utf-8').strip()
        latex_output = latex_output.replace('\\tightlist\n', '')
        return latex_output
    except FileNotFoundError:
        print("❌ Erro: Pandoc não encontrado. Certifique-se de que está instalado e no PATH.")
        print("Por favor, instale Pandoc em: https://pandoc.org/installing.html")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao converter Markdown para LaTeX com Pandoc: {e}")
        print(f"Stderr: {e.stderr.decode('utf-8')}")
        return markdown_text 


def gerar_latex(projeto: str, idioma_arg: str):
    start_time = time.time()
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}] ▶️ Iniciando etapa: Gerar LaTeX para o projeto '{projeto}' ({idioma_arg})...")

    base_dir = Path("projetos") / projeto
    config_path = base_dir / "config.json"
    
    templates_dir = base_dir / "templates" / "tex"
    estilos_config_path = base_dir / "estilos" / "estilo_livro.json"
    
    # --- Normalização do Idioma ---
    if idioma_arg.lower() == "pt-br":
        idioma_normalizado_para_path = "pt-BR"
        idioma_para_latex = "brazil"
    elif idioma_arg.lower() == "en":
        idioma_normalizado_para_path = "en-US"
        idioma_para_latex = "english"
    else:
        idioma_normalizado_para_path = idioma_arg
        idioma_para_latex = "english" 

    # --- NOVA PASTA PARA ARQUIVOS LATEX GERADOS ---
    latex_output_dir = base_dir / "gerado_automaticamente" / idioma_normalizado_para_path / "tex"
    latex_output_dir.mkdir(parents=True, exist_ok=True)
    
    # --- NOVO NOME PARA O ARQUIVO .TEX PARA EVITAR CONFLITOS ---
    output_tex_filename = "livro_completo_para_latex.tex" 
    output_tex_path = latex_output_dir / output_tex_filename

    # Criar a pasta 'output' para o PDF final (caso não exista)
    pdf_final_output_dir = base_dir / "output" / idioma_normalizado_para_path
    pdf_final_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"  Caminhos configurados:")
    print(f"    Diretório Base do Projeto: {base_dir.resolve()}")
    print(f"    Arquivo de Configuração: {config_path.resolve()}")
    print(f"    Diretório de Templates LaTeX: {templates_dir.resolve()}")
    print(f"    Arquivo de Estilos: {estilos_config_path.resolve()}")
    print(f"    Diretório de Saída LaTeX: {latex_output_dir.resolve()}")
    print(f"    Arquivo LaTeX de Saída: {output_tex_path.resolve()}")
    print(f"    Diretório de Saída do PDF Final: {pdf_final_output_dir.resolve()}")


    if not config_path.exists():
        print(f"❌ Arquivo de configuração não encontrado: {config_path.resolve()}")
        return

    if not templates_dir.exists():
        print(f"❌ Diretório de templates LaTeX não encontrado: {templates_dir.resolve()}")
        print(f"Por favor, crie a pasta: {templates_dir.resolve()}")
        return
    
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=False)

    config_data = json.loads(config_path.read_text(encoding="utf-8"))
    titulo_livro = config_data.get("titulo", "Livro Digital")
    autor_livro = config_data.get("autor", "Autor Desconhecido")
    
    raw_styles_data = {}
    if estilos_config_path.exists():
        try:
            raw_styles_data = json.loads(estilos_config_path.read_text(encoding="utf-8"))
            print(f"✅ Estilos carregados de: {estilos_config_path.resolve()}")
        except json.JSONDecodeError as e:
            print(f"❌ Erro ao carregar estilos de {estilos_config_path.resolve()}: {e}")
            print("Usando estilos padrão/fallback para continuar.")
    else:
        print(f"⚠️ Arquivo de estilos não encontrado em: {estilos_config_path.resolve()}. Usando estilos padrão/fallback.")
    
    processed_styles = {}

    p_def = raw_styles_data.get("paragraph_default", {})
    processed_styles["paragraph_default_font_size_pt"] = parse_dimension(p_def.get("font-size", "10pt"), 10.0)
    processed_styles["paragraph_default_text_indent_cm"] = parse_dimension(p_def.get("text-indent", "0.5cm"), 0.5)
    processed_styles["paragraph_default_line_height"] = float(p_def.get("line-height", "1.2"))
    processed_styles["paragraph_default_margin_bottom_cm"] = parse_dimension(p_def.get("margin-bottom", "0.2cm"), 0.2)
    processed_styles["paragraph_default_font_family"] = p_def.get("font-family", "Latin Modern Roman")
    processed_styles["paragraph_default_color_name"] = p_def.get("color", "text_gray")

    h1_def = raw_styles_data.get("heading_1", {})
    processed_styles["heading_1_font_size_pt"] = parse_dimension(h1_def.get("font-size", "24pt"), 24.0)
    processed_styles["heading_1_line_spacing_pt"] = round(processed_styles["heading_1_font_size_pt"] * 1.2, 2)
    processed_styles["heading_1_font_family"] = h1_def.get("font-family", "Latin Modern Sans")
    processed_styles["heading_1_color_name"] = h1_def.get("color", "DarkBlueHeading")
    processed_styles["heading_1_margin_top_cm"] = parse_dimension(h1_def.get("margin-top", "1cm"), 1.0)
    processed_styles["heading_1_margin_bottom_cm"] = parse_dimension(h1_def.get("margin-bottom", "0.5cm"), 0.5)

    processed_styles["document_margins_cm"] = parse_dimension(raw_styles_data.get("document_margins", "2.5cm"), 2.5)

    default_colors = {
        "text_gray": "333333",
        "DarkBlueHeading": "000080"
    }
    processed_colors = {}
    for name, hex_val in raw_styles_data.get("colors", {}).items():
        if isinstance(hex_val, str) and hex_val.startswith("#"):
            processed_colors[name] = hex_val[1:]
        else:
            processed_colors[name] = hex_val
    processed_styles["colors"] = {**default_colors, **processed_colors}


    livro_path = base_dir / "gerado_automaticamente" / idioma_normalizado_para_path / "livro_estruturado.json"
    if not livro_path.exists():
        print(f"❌ Arquivo livro_estruturado.json não encontrado: {livro_path.resolve()}")
        return
    livro_data = json.loads(livro_path.read_text(encoding="utf-8"))

    processed_content = {
        "title": titulo_livro,
        "author": autor_livro,
        "sections": []
    }
    
    for item in livro_data.get("conteudo", []):
        section_content_latex = []
        if "corpo_do_texto" in item and isinstance(item["corpo_do_texto"], list):
            full_markdown_block = "\n\n".join(item["corpo_do_texto"])
            latex_converted_text = convert_markdown_to_latex(full_markdown_block)
            section_content_latex.append({
                "type": "raw_latex",
                "text": latex_converted_text
            })
        
        if item["tipo"] == "parte":
            processed_content["sections"].append({
                "type": "heading_part",
                "text": clean_title_for_output(item.get("titulo_parte", f"Parte {len(processed_content['sections']) + 1}")),
                "content": section_content_latex
            })
        elif item["tipo"] == "capitulo":
            processed_content["sections"].append({
                "type": "heading_1",
                "text": clean_title_for_output(item.get("titulo1", f"Capítulo {len(processed_content['sections']) + 1}")),
                "content": section_content_latex
            })
    
    base_latex_tpl = env.get_template("base.tex.j2")
    latex_content = base_latex_tpl.render(
        styles=processed_styles,
        content=processed_content,
        lang=idioma_para_latex
    )

    with open(output_tex_path, "w", encoding="utf-8") as f:
        f.write(latex_content)

    end_time = time.time()
    print(f"✅ Arquivo LaTeX gerado com sucesso em: {output_tex_path.resolve()}")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}] ✅ Etapa 'Gerar LaTeX' concluída em {end_time - start_time:.2f} segundos.")
    # REMOVIDA: print(f"Para gerar o PDF, execute 'latex_para_pdf.py' apontando para este arquivo.")


def main():
    parser = argparse.ArgumentParser(description="Gera a versão LaTeX de um projeto de livro.")
    parser.add_argument("--projeto", required=True, help="Nome do diretório do projeto (ex: liderando_transformacao)")
    parser.add_argument("--idioma", default="pt-BR", help="Idioma do livro (ex: pt-BR, en-US).")
    args = parser.parse_args()

    gerar_latex(args.projeto, args.idioma)


if __name__ == "__main__":
    main()
