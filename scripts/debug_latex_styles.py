# scripts/debug_latex_styles.py
import json
from pathlib import Path
import argparse

def debug_latex_styles(project_name: str, lang: str):
    base_path = Path("projetos") / project_name
    config_path = base_path / "config.json"

    if not config_path.exists():
        print(f"❌ Erro: config.json não encontrado para o projeto '{project_name}'. Caminho esperado: {config_path}")
        return

    config = json.loads(config_path.read_text(encoding="utf-8"))

    styles_file_path = base_path / config["estilos"]
    if not styles_file_path.exists():
        print(f"❌ Erro: Arquivo de estilos '{config['estilos']}' não encontrado. Caminho esperado: {styles_file_path}. Verifique o 'estilos' no config.json.")
        return

    styles_data = json.loads(styles_file_path.read_text(encoding="utf-8"))

    # O processamento real dos estilos ocorre em 'gerar_latex.py'
    # Aqui, vamos simular como os dados seriam usados pelo styles.tex.j2
    # Supondo que o styles.json tem a estrutura raiz dos estilos, por exemplo:
    # { "paragraph_default": {...}, "heading_1": {...}, "colors": {...} }
    processed_styles = styles_data 
    # Se styles.json tiver uma chave raiz "estilos", use: processed_styles = styles_data.get("estilos", {})

    print(f"--- DEPURAÇÃO DE ESTILOS LATEX PARA O PROJETO '{project_name}', IDIOMA '{lang}' ---")
    print("\n--- CORES ---")
    latex_colors = []
    if processed_styles.get("colors"):
        print("Cores personalizadas encontradas no styles.json:")
        for name, hex_code in processed_styles["colors"].items():
            latex_colors.append(f"\\definecolor{{{name}}}{{HTML}}{{{hex_code.replace('#', '')}}}")
    else:
        print("Nenhuma cor personalizada definida. Usando cores padrão:")
        latex_colors.append("\\definecolor{text_gray}{HTML}{333333}")
        latex_colors.append("\\definecolor{DarkBlueHeading}{HTML}{000080}")

    for line in latex_colors:
        print(line)

    print("\n--- FONTES (Principal e Sans) ---")
    latex_fonts = []
    paragraph_default = processed_styles.get("paragraph_default", {})
    if paragraph_default and paragraph_default.get("font-family"):
        latex_fonts.append(f"\\setmainfont{{{paragraph_default['font-family']}}}")
    else:
        latex_fonts.append("\\setmainfont{Latin Modern Roman}")

    heading_1 = processed_styles.get("heading_1", {})
    if heading_1 and heading_1.get("font-family"):
        latex_fonts.append(f"\\setsansfont{{{heading_1['font-family']}}}")
    else:
        latex_fonts.append("\\setsansfont{Latin Modern Sans}")

    for line in latex_fonts:
        print(line)

    print("\n--- CONFIGURAÇÕES DE PARÁGRAFO ---")
    latex_paragraph = []

    par_indent = paragraph_default.get("text-indent")
    if par_indent:
        latex_paragraph.append(f"\\setlength{{\\parindent}}{{{par_indent}}}")
    else:
        # Assumindo que você pode ter 'text_indent' ou um valor padrão para fallback
        latex_paragraph.append(f"\\setlength{{\\parindent}}{{{paragraph_default.get('text_indent', '0.5cm')}}}") 

    par_margin_bottom = paragraph_default.get("margin-bottom")
    if par_margin_bottom:
        latex_paragraph.append(f"\\setlength{{\\parskip}}{{{par_margin_bottom}}}")
        latex_paragraph.append(f"\\DeclareRobustCommand{{\\paragraphbreak}}{{\\vspace{{{par_margin_bottom}}}\\noindent}}")
    else:
        # Assumindo 'margin_bottom' ou um valor padrão para fallback
        default_margin_bottom = paragraph_default.get('margin_bottom', '0.2cm') 
        latex_paragraph.append(f"\\setlength{{\\parskip}}{{{default_margin_bottom}}}")
        latex_paragraph.append(f"\\DeclareRobustCommand{{\\paragraphbreak}}{{\\vspace{{{default_margin_bottom}}}\\noindent}}")

    for line in latex_paragraph:
        print(line)

    print("\n--- CONFIGURAÇÕES DE TÍTULOS H1 (SECTION) (Representação Parcial) ---")
    latex_heading = []

    h1_font_size = heading_1.get("font-size")
    h1_line_spacing = heading_1.get("line-spacing")
    h1_margin_top = heading_1.get("margin-top")
    h1_margin_bottom = heading_1.get("margin-bottom")

    # Esta é uma representação simplificada da lógica complexa de \titleformat
    latex_heading.append(f"\\fontsize{{ {h1_font_size if h1_font_size else '24pt'} }}{{ {h1_line_spacing if h1_line_spacing else '28.8pt'} }}\\selectfont")
    latex_heading.append(f"\\titlespacing*{{\\section}}{{0pt}}{{ {h1_margin_top if h1_margin_top else '1.0cm'} }}{{ {h1_margin_bottom if h1_margin_bottom else '0.5cm'} }}")

    for line in latex_heading:
        print(line)

    print("\n--- FIM DA DEPURAÇÃO DE ESTILOS ---")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Debuga o mapeamento de estilos JSON para LaTeX.")
    parser.add_argument("--projeto", required=True, help="Nome do projeto (ex: liderando_transformacao)")
    parser.add_argument("--idioma", default="pt-BR", help="Idioma (ex: pt-BR)") 

    args = parser.parse_args()
    debug_latex_styles(args.projeto, args.idioma)
