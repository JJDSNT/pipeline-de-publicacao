# scripts/verify_latex_output.py
import json
from pathlib import Path
import argparse
import datetime
import re

def verify_latex_output(project_name: str, lang: str):
    base_path = Path("projetos") / project_name

    # --- Carrega Configurações e Dados JSON ---
    config_path = base_path / "config.json"
    if not config_path.exists():
        print(f"❌ Erro: config.json não encontrado para o projeto '{project_name}'. Caminho esperado: {config_path}")
        return False
    config = json.loads(config_path.read_text(encoding="utf-8"))

    styles_file_path = base_path / "estilos" / "estilo_livro.json" # Caminho fixo conforme gerar_latex.py
    if not styles_file_path.exists():
        print(f"❌ Erro: Arquivo de estilos '{styles_file_path}' não encontrado. Caminho esperado: {styles_file_path}.")
        return False
    styles_data = json.loads(styles_file_path.read_text(encoding="utf-8"))

    # Metadados são lidos diretamente do config.json, não de um arquivo separado
    expected_title = config.get("titulos", {}).get("TITULO_PRINCIPAL", "Livro Digital")
    expected_author = config.get("autor", "Autor Desconhecido")
    data_publicacao_from_config = config.get("data_publicacao", "")

    # Simula a data atual no formato usado na geração, se data_publicacao não for especificada
    today_formatted = datetime.date.today().strftime("%d de %B de %Y")
    expected_date_for_comparison = data_publicacao_from_config if data_publicacao_from_config else today_formatted

    # --- Carrega o Conteúdo do Arquivo .tex Gerado ---
    generated_tex_path = base_path / "gerado_automaticamente" / lang / "tex" / "livro_completo_para_latex.tex"
    if not generated_tex_path.exists():
        print(f"❌ Erro: Arquivo .tex gerado não encontrado. Por favor, execute 'gerar_latex.py' primeiro. Caminho esperado: {generated_tex_path}")
        return False
    generated_tex_content = generated_tex_path.read_text(encoding="utf-8")

    print(f"--- VERIFICAÇÃO DO ARQUIVO LATEX GERADO PARA '{project_name}', IDIOMA '{lang}' ---")
    print(f"Verificando: {generated_tex_path.resolve()}")

    overall_status = True

    # --- VERIFICAÇÃO DE METADADOS (Título, Autor, Data) ---
    print("\n--- Verificando Metadados do Livro ---")

    # Título
    title_match = re.search(r"\\title\{(.*?)\}", generated_tex_content)
    if title_match and title_match.group(1).strip() == expected_title.strip():
        print(f"✅ Título encontrado e corresponde: '{title_match.group(1)}'")
    else:
        print(f"❌ Título NÃO corresponde ou não encontrado. Esperado: '{expected_title}', Encontrado: '{title_match.group(1) if title_match else 'NÃO ENCONTRADO'}'")
        overall_status = False

    # Autor
    author_match = re.search(r"\\author\{(.*?)\}", generated_tex_content)
    if author_match and author_match.group(1).strip() == expected_author.strip():
        print(f"✅ Autor encontrado e corresponde: '{author_match.group(1)}'")
    else:
        print(f"❌ Autor NÃO corresponde ou não encontrado. Esperado: '{expected_author}', Encontrado: '{author_match.group(1) if author_match else 'NÃO ENCONTRADO'}'")
        overall_status = False

    # Data
    date_match = re.search(r"\\date\{(.*?)\}", generated_tex_content)
    if date_match and date_match.group(1).strip() == expected_date_for_comparison.strip():
        print(f"✅ Data encontrada e corresponde: '{date_match.group(1)}'")
    else:
        print(f"❌ Data NÃO corresponde ou não encontrada. Esperado: '{expected_date_for_comparison}', Encontrado: '{date_match.group(1) if date_match else 'NÃO ENCONTRADO'}'")
        overall_status = False

    # Maketitle
    if "\\maketitle" in generated_tex_content:
        print("✅ Comando \\maketitle encontrado.")
    else:
        print("❌ Comando \\maketitle NÃO encontrado. A página de título pode não ser gerada.")
        overall_status = False

    # --- VERIFICAÇÃO DE CORES ---
    print("\n--- Verificando Cores Personalizadas ---")
    custom_colors_found = False
    if "colors" in styles_data and styles_data["colors"]:
        for name, hex_code in styles_data["colors"].items():
            expected_latex_color = f"\\definecolor{{{name}}}{{HTML}}{{{hex_code.replace('#', '')}}}"
            if expected_latex_color in generated_tex_content:
                print(f"✅ Cor '{name}' encontrada: {expected_latex_color}")
                custom_colors_found = True
            else:
                print(f"❌ Cor '{name}' NÃO encontrada como esperado: {expected_latex_color}")
                overall_status = False
        if custom_colors_found:
            print("✅ Pelo menos uma cor personalizada do styles.json foi encontrada.")
        else:
            print("❌ Nenhuma cor personalizada do styles.json foi encontrada. Verificando fallbacks...")
    else:
        print("ℹ️ Nenhuma seção 'colors' ou seção 'colors' vazia no styles.json. Verificando cores padrão.")

    # Verifica cores padrão, se não houver personalizadas ou se as personalizadas falharam
    default_colors = {
        "text_gray": "333333",
        "DarkBlueHeading": "000080"
    }
    all_defaults_found = True
    for name, hex_code in default_colors.items():
        expected_latex_default_color = f"\\definecolor{{{name}}}{{HTML}}{{{hex_code}}}"
        if expected_latex_default_color in generated_tex_content:
            print(f"✅ Cor padrão '{name}' encontrada: {expected_latex_default_color}")
        else:
            print(f"❌ Cor padrão '{name}' NÃO encontrada: {expected_latex_default_color}")
            all_defaults_found = False
            # overall_status = False # Não setar false aqui se o esperado era personalizar

    # --- VERIFICAÇÃO DE FONTES ---
    print("\n--- Verificando Fontes ---")
    expected_main_font = styles_data.get("paragraph_default", {}).get("font-family", "Latin Modern Roman")
    main_font_match = re.search(r"\\setmainfont(?:\[.*?\])?\{(.*?)\}", generated_tex_content)
    if main_font_match and main_font_match.group(1).strip() == expected_main_font.strip():
        print(f"✅ Fonte principal encontrada e corresponde: '{main_font_match.group(1)}'")
    else:
        print(f"❌ Fonte principal NÃO corresponde ou não encontrada. Esperado: '{expected_main_font}', Encontrado: '{main_font_match.group(1) if main_font_match else 'NÃO ENCONTRADO'}'")
        overall_status = False

    expected_sans_font = styles_data.get("heading_1", {}).get("font-family", "Latin Modern Sans")
    sans_font_match = re.search(r"\\setsansfont(?:\[.*?\])?\{(.*?)\}", generated_tex_content)
    if sans_font_match and sans_font_match.group(1).strip() == expected_sans_font.strip():
        print(f"✅ Fonte sans-serif encontrada e corresponde: '{sans_font_match.group(1)}'")
    else:
        print(f"❌ Fonte sans-serif NÃO corresponde ou não encontrada. Esperado: '{expected_sans_font}', Encontrado: '{sans_font_match.group(1) if sans_font_match else 'NÃO ENCONTRADO'}'")
        overall_status = False

    # --- VERIFICAÇÃO DE CONFIGURAÇÕES DE PARÁGRAFO ---
    print("\n--- Verificando Configurações de Parágrafo ---")
    paragraph_default = styles_data.get("paragraph_default", {})

    expected_parindent = paragraph_default.get("text-indent", paragraph_default.get("text_indent", "0.5cm"))
    parindent_match = re.search(r"\\setlength\{\\parindent\}\{(" + re.escape(expected_parindent.replace(" ", r"\s*")) + r")\}", generated_tex_content)
    if parindent_match:
        print(f"✅ Parágrafo indentação encontrada: '{parindent_match.group(1)}'")
    else:
        print(f"❌ Parágrafo indentação NÃO encontrada como esperado: '{expected_parindent}'")
        overall_status = False

    expected_parskip = paragraph_default.get("margin-bottom", paragraph_default.get("margin_bottom", "0.2cm"))
    parskip_match = re.search(r"\\setlength\{\\parskip\}\{(" + re.escape(expected_parskip.replace(" ", r"\s*")) + r")\}", generated_tex_content)
    if parskip_match:
        print(f"✅ Parágrafo skip encontrada: '{parskip_match.group(1)}'")
    else:
        print(f"❌ Parágrafo skip NÃO encontrada como esperado: '{expected_parskip}'")
        overall_status = False

    # Verifica o comando \paragraphbreak
    paragraphbreak_match = re.search(r"\\DeclareRobustCommand\{\\paragraphbreak\}\{\\vspace\{(" + re.escape(expected_parskip.replace(" ", r"\s*")) + r")\}\\noindent\}", generated_tex_content)
    if paragraphbreak_match:
        print(f"✅ Comando \\paragraphbreak encontrado com valor: '{paragraphbreak_match.group(1)}'")
    else:
        print(f"❌ Comando \\paragraphbreak NÃO encontrado ou com valor incorreto. Esperado valor de '{expected_parskip}'")
        overall_status = False

    # --- VERIFICAÇÃO DE CONFIGURAÇÕES DE TÍTULOS H1 ---
    print("\n--- Verificando Configurações de Títulos H1 (Section) ---")
    heading_1 = styles_data.get("heading_1", {})

    expected_h1_font_size = heading_1.get("font-size", "24pt")
    expected_h1_line_spacing = heading_1.get("line-spacing", "28.8pt")

    fontsize_match = re.search(r"\\fontsize\{(" + re.escape(expected_h1_font_size.replace(" ", r"\s*")) + r")\}\{(" + re.escape(expected_h1_line_spacing.replace(" ", r"\s*")) + r")\}\\selectfont", generated_tex_content)
    if fontsize_match:
        print(f"✅ Tamanho da fonte H1 encontrado: '{fontsize_match.group(1)}', Espaçamento da linha H1: '{fontsize_match.group(2)}'")
    else:
        print(f"❌ Tamanho da fonte H1 ou Espaçamento da linha H1 NÃO encontrados como esperado. Esperado: '{expected_h1_font_size}', '{expected_h1_line_spacing}'")
        overall_status = False

    expected_h1_margin_top = heading_1.get("margin-top", "1.0cm")
    expected_h1_margin_bottom = heading_1.get("margin-bottom", "0.5cm")

    titlespacing_match = re.search(r"\\titlespacing\*\{\\section\}\{0pt\}\{(" + re.escape(expected_h1_margin_top.replace(" ", r"\s*")) + r")\}\{(" + re.escape(expected_h1_margin_bottom.replace(" ", r"\s*")) + r")\}", generated_tex_content)
    if titlespacing_match:
        print(f"✅ Margens do título H1 encontradas: Top '{titlespacing_match.group(1)}', Bottom '{titlespacing_match.group(2)}'")
    else:
        print(f"❌ Margens do título H1 NÃO encontradas como esperado. Esperado: Top '{expected_h1_margin_top}', Bottom '{expected_h1_margin_bottom}'")
        overall_status = False

    print("\n--- FIM DA VERIFICAÇÃO ---")
    if overall_status:
        print("✅ TODAS as verificações importantes passaram. O arquivo LaTeX gerado parece estar correto com os dados JSON.")
    else:
        print("❌ ALGUMAS verificações falharam. Revise os erros acima para depuração.")
    return overall_status

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verifica se as variáveis dos arquivos JSON foram corretamente injetadas no arquivo LaTeX gerado.")
    parser.add_argument("--projeto", required=True, help="Nome do projeto (ex: liderando_transformacao)")
    parser.add_argument("--idioma", default="pt-BR", help="Idioma (ex: pt-BR)")

    args = parser.parse_args()
    verify_latex_output(args.projeto, args.idioma)
