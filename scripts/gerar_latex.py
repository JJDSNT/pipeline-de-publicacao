# scripts/gerar_latex.py
import argparse
import json
from pathlib import Path
import sys
import re
import subprocess
import time
import datetime # Importar datetime para a data atual

from jinja2 import Environment, FileSystemLoader, select_autoescape

# Adiciona o diretório raiz do projeto ao sys.path para importações
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from utils.cleaner import clean_title_for_output
from utils.filters import setup_jinja_env_with_filters # Importa a função de setup de filtros

def parse_dimension(value: str, default: float) -> float:
    """Extrai o valor numérico de uma string de dimensão (ex: '2.5cm' -> 2.5)."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        match = re.match(r"([0-9.]+)([a-zA-Z]+)", value.strip())
        if match:
            return float(match.group(1))
    return default

def sanitize_filename(text: str) -> str:
    """
    Sanitiza uma string para ser usada como nome de arquivo, removendo caracteres inválidos.
    Converte espaços e outros caracteres em hífens simples.
    """
    # Remove caracteres que não são letras, números, espaços ou hífens/sublinhados
    sanitized = re.sub(r'[^\w\s-]', '', text).strip()
    # Substitui múltiplos espaços/hífens/sublinhados por um único sublinhado
    sanitized = re.sub(r'[\s_-]+', '_', sanitized).lower()
    return sanitized


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
        # A remoção do emoji será feita pelo filtro escape_latex no Jinja2 agora,
        # mas mantemos aqui por segurança se esta função for usada isoladamente.
        latex_output = latex_output.replace('📌', '')
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

    # --- NOVO: Diretorios de Saída para os arquivos LaTeX modulares ---
    latex_output_root_dir = base_dir / "gerado_automaticamente" / idioma_normalizado_para_path / "tex"
    latex_output_setup_dir = latex_output_root_dir / "setup"
    latex_output_content_dir = latex_output_root_dir / "content"

    # Garantir que todos os diretórios de saída existam
    latex_output_root_dir.mkdir(parents=True, exist_ok=True)
    latex_output_setup_dir.mkdir(parents=True, exist_ok=True)
    latex_output_content_dir.mkdir(parents=True, exist_ok=True)

    # --- NOVO NOME PARA O ARQUIVO .TEX PRINCIPAL ---
    # Este será o arquivo que o xelatex irá compilar
    output_main_tex_filename = "livro_completo_para_latex.tex"
    output_main_tex_path = latex_output_root_dir / output_main_tex_filename

    # Criar a pasta 'output' para o PDF final (caso não exista)
    pdf_final_output_dir = base_dir / "output" / idioma_normalizado_para_path
    pdf_final_output_dir.mkdir(parents=True, exist_ok=True)

    print(f"    Caminhos configurados:")
    print(f"      Diretório Base do Projeto: {base_dir.resolve()}")
    print(f"      Arquivo de Configuração: {config_path.resolve()}")
    print(f"      Diretório de Templates LaTeX: {templates_dir.resolve()}")
    print(f"      Arquivo de Estilos: {estilos_config_path.resolve()}")
    print(f"      Diretório de Saída LaTeX Raiz: {latex_output_root_dir.resolve()}")
    print(f"      Diretório de Saída LaTeX Setup: {latex_output_setup_dir.resolve()}")
    print(f"      Diretório de Saída LaTeX Conteúdo: {latex_output_content_dir.resolve()}")
    print(f"      Arquivo LaTeX Principal de Saída: {output_main_tex_path.resolve()}")
    print(f"      Diretório de Saída do PDF Final: {pdf_final_output_dir.resolve()}")


    if not config_path.exists():
        print(f"❌ Arquivo de configuração não encontrado: {config_path.resolve()}")
        return

    if not templates_dir.exists():
        print(f"❌ Diretório de templates LaTeX não encontrado: {templates_dir.resolve()}")
        print(f"Por favor, crie a pasta: {templates_dir.resolve()}")
        return

    # Configurar Jinja2 Environment
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(['html', 'xml', 'tex']), # Certifique-se de que 'tex' está aqui
        trim_blocks=True,
        lstrip_blocks=True
    )
    env = setup_jinja_env_with_filters(env) # Aplica os filtros, incluindo escape_latex

    config_data = json.loads(config_path.read_text(encoding="utf-8"))
    # Ajustado para ler do seu config.json
    titulo_livro = config_data.get("titulos", {}).get("TITULO_PRINCIPAL", "Livro Digital")
    autor_livro = config_data.get("autor", "Autor Desconhecido")
    data_publicacao_config = config_data.get("data_publicacao", "") # Para metadados no template

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

    # Processar estilos de parágrafo
    p_def = raw_styles_data.get("paragraph_default", {})
    processed_styles["paragraph_default"] = {
        "font-size": parse_dimension(p_def.get("font-size", "10pt"), 10.0),
        "text-indent": parse_dimension(p_def.get("text-indent", "0.5cm"), 0.5),
        "line-height": float(p_def.get("line-height", "1.2")),
        "margin-bottom": parse_dimension(p_def.get("margin-bottom", "0.2cm"), 0.2),
        "font-family": p_def.get("font-family", "Latin Modern Roman"),
        "color": p_def.get("color", "text_gray")
    }

    # Processar estilos de heading_1
    h1_def = raw_styles_data.get("heading_1", {})
    processed_styles["heading_1"] = {
        "font-size": parse_dimension(h1_def.get("font-size", "24pt"), 24.0),
        "line-spacing": round(parse_dimension(h1_def.get("line-spacing", "28.8pt"), 28.8), 2), # Adicionado line-spacing para ser dinâmico
        "font-family": h1_def.get("font-family", "Latin Modern Sans"),
        "color": h1_def.get("color", "DarkBlueHeading"),
        "margin-top": parse_dimension(h1_def.get("margin-top", "1cm"), 1.0),
        "margin-bottom": parse_dimension(h1_def.get("margin-bottom", "0.5cm"), 0.5)
    }

    # Processar margens do documento
    processed_styles["document_margins_cm"] = parse_dimension(raw_styles_data.get("document_margins", "2.5cm"), 2.5)
    processed_styles["document_settings"] = raw_styles_data.get("document_settings", {}) # Para margens dinâmicas

    # --- INÍCIO DA LÓGICA DE PROCESSAMENTO DE CORES ATUALIZADA ---
    processed_colors = {}
    
    # Coleta todas as cores definidas no metadata do estilo_livro.json
    if "metadata" in raw_styles_data and isinstance(raw_styles_data["metadata"], dict):
        for color_group_key in ["cores_texto", "cores_fundo_destaque", "cores_borda_destaque"]:
            if color_group_key in raw_styles_data["metadata"] and isinstance(raw_styles_data["metadata"][color_group_key], dict):
                for name, hex_val in raw_styles_data["metadata"][color_group_key].items():
                    if isinstance(hex_val, str) and hex_val.startswith("#"):
                        processed_colors[name] = hex_val[1:]
                    else:
                        # Se não for uma string de hex com '#', armazena como está
                        # Cuidado: isto pode causar problemas se hex_val não for um formato válido para LaTeX
                        processed_colors[name] = hex_val 
    
    # Garantir que cores essenciais tenham um fallback (caso não estejam nas cores do metadata)
    # Estas sobrescreverão qualquer cor de mesmo nome coletada do metadata, se existirem
    processed_colors["text_gray"] = processed_colors.get("text_gray", "333333")
    processed_colors["DarkBlueHeading"] = processed_colors.get("DarkBlueHeading", "000080")
    
    processed_styles["colors"] = processed_colors

    # Gerar definições de cores LaTeX para injeção no template de estilos
    custom_color_definitions = []
    for color_name, hex_value in processed_styles["colors"].items():
        # Assegura que hex_value seja uma string e remova '#' se presente
        final_hex = hex_value.replace("#", "") if isinstance(hex_value, str) else str(hex_value)
        custom_color_definitions.append(f"\\definecolor{{{color_name}}}{{HTML}}{{{final_hex}}}")
    processed_styles["custom_color_definitions"] = "\n".join(custom_color_definitions)
    # --- FIM DA LÓGICA DE PROCESSAMENTO DE CORES ATUALIZADA ---


    livro_path = base_dir / "gerado_automaticamente" / idioma_normalizado_para_path / "livro_estruturado.json"
    if not livro_path.exists():
        print(f"❌ Arquivo livro_estruturado.json não encontrado: {livro_path.resolve()}")
        return
    livro_data = json.loads(livro_path.read_text(encoding="utf-8"))

    # Preparar dados de conteúdo para os templates
    processed_content = {
        "title": titulo_livro,
        "author": autor_livro,
        "sections": [] # Esta lista será populada com os dados brutos das seções
    }

    # Processar o conteúdo do livro para LaTeX e preparar para templates modulares
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

    # --- NOVO: Renderizar e Salvar os Arquivos Modulares ---

    # Prepara os metadados para o template, usando os dados do config.json
    metadados_for_template = {
        "titulo_livro": titulo_livro,
        "autor": autor_livro,
        "data_publicacao": data_publicacao_config,
        "descricao": config_data.get("descricao", ""),
        "palavras_chave": config_data.get("palavras_chave", []),
        "licenca": config_data.get("licenca", "")
    }

    # Contexto base para todos os templates
    base_context = {
        'lang': idioma_para_latex,
        'content': processed_content, # Passa o content_data completo para todos os templates
        'styles': processed_styles,
        'custom_color_definitions': processed_styles["custom_color_definitions"],
        'metadados': metadados_for_template, # AGORA 'metadados' ESTÁ NO CONTEXTO
        'hoje': datetime.date.today().strftime("%d de %B de %Y"), # Garante que 'hoje' está no contexto
        'config': config_data # Opcional: passa o config_data completo também
    }

    # 1. Renderizar setup/packages.tex
    packages_template = env.get_template('setup/packages.tex.j2')
    packages_output = packages_template.render(base_context)
    with open(latex_output_setup_dir / 'packages.tex', 'w', encoding='utf-8') as f:
        f.write(packages_output)
    print(f"✅ Gerado: {latex_output_setup_dir / 'packages.tex'}")

    # 2. Renderizar setup/configurations.tex
    configurations_template = env.get_template('setup/configurations.tex.j2')
    configurations_output = configurations_template.render(base_context)
    with open(latex_output_setup_dir / 'configurations.tex', 'w', encoding='utf-8') as f:
        f.write(configurations_output)
    print(f"✅ Gerado: {latex_output_setup_dir / 'configurations.tex'}")

    # 3. Renderizar setup/styles.tex
    styles_template = env.get_template('setup/styles.tex.j2')
    styles_output = styles_template.render(base_context)
    with open(latex_output_setup_dir / 'styles.tex', 'w', encoding='utf-8') as f:
        f.write(styles_output)
    print(f"✅ Gerado: {latex_output_setup_dir / 'styles.tex'}")

    # 4. Renderizar arquivos de seção individuais (content/*.tex)
    section_files_generated = [] # Lista para armazenar os nomes dos arquivos de seção gerados
    section_item_template = env.get_template('content/section_item.tex.j2')

    for i, section_data in enumerate(processed_content['sections']):
        # Gera um nome de arquivo sanitizado baseado no tipo e título da seção
        # Adiciona um índice para garantir unicidade
        section_filename_base = f"{section_data['type']}_{sanitize_filename(section_data['text'])}"
        section_filename = f"{section_filename_base}_{i+1}.tex"

        # Renderiza o template de item de seção com os dados da seção atual
        section_output = section_item_template.render(section=section_data)
        section_filepath = latex_output_content_dir / section_filename

        with open(section_filepath, 'w', encoding='utf-8') as f:
            f.write(section_output)

        section_files_generated.append(section_filename)
        print(f"✅ Gerado: {section_filepath}")

    # Adicionar a lista de nomes de arquivos de seção gerados ao contexto para main_content.tex.j2
    base_context['section_files'] = section_files_generated

    # 5. Renderizar content/main_content.tex
    main_content_template = env.get_template('content/main_content.tex.j2')
    main_content_output = main_content_template.render(base_context)
    with open(latex_output_content_dir / 'main_content.tex', 'w', encoding='utf-8') as f:
        f.write(main_content_output)
    print(f"✅ Gerado: {latex_output_content_dir / 'main_content.tex'}")

    # 6. Renderizar o arquivo principal (main.tex)
    main_template = env.get_template('main.tex.j2')
    latex_output = main_template.render(base_context)
    with open(output_main_tex_path, "w", encoding="utf-8") as f:
        f.write(latex_output)

    end_time = time.time()
    print(f"✅ Arquivo LaTeX principal gerado com sucesso em: {output_main_tex_path.resolve()}")
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}] ✅ Etapa 'Gerar LaTeX' concluída em {end_time - start_time:.2f} segundos.")


def main():
    parser = argparse.ArgumentParser(description="Gera a versão LaTeX de um projeto de livro.")
    parser.add_argument("--projeto", required=True, help="Nome do diretório do projeto (ex: liderando_transformacao)")
    parser.add_argument("--idioma", default="pt-BR", help="Idioma do livro (ex: pt-BR, en-US).")
    args = parser.parse_args()

    gerar_latex(args.projeto, args.idioma)


if __name__ == "__main__":
    main()
