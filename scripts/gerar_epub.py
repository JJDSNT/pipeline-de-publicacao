# scripts/gerar_epub.py

import argparse
import json
import zipfile
from pathlib import Path
from typing import Dict, Any, List
from datetime import date
import sys # Importar o módulo sys para manipular o caminho de busca do Python

from jinja2 import Environment, FileSystemLoader

# --- Início da correção para o ModuleNotFoundError (mantida da última vez) ---
# Adiciona a raiz do projeto ao sys.path
# Isso permite que módulos em diretórios irmãos (como 'utils') sejam importados.
script_dir = Path(__file__).resolve().parent # Obtém o diretório do script atual (scripts/)
project_root = script_dir.parent            # Sobe um nível para chegar à raiz do projeto
sys.path.insert(0, str(project_root))       # Adiciona a raiz do projeto ao início do sys.path
# --- Fim da correção ---

# Importa as funções de limpeza (ainda necessárias para os títulos no TOC)
from utils.cleaner import clean_title_for_output, clean_content_text


class GerenciadorEstilos:
    def __init__(self, config_path: Path):
        self.config = self._carregar_config(config_path)
        self.estilos = self.config["estilos"]

    def _carregar_config(self, path: Path) -> Dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def obter_estilo_epub(self, nome_estilo: str) -> Dict[str, Any]:
        if nome_estilo not in self.estilos:
            raise ValueError(f"Estilo '{nome_estilo}' não encontrado")
        return self.estilos[nome_estilo]["epub"]

    def gerar_css_completo(self) -> str:
        css_lines = []

        css_global = self.config["configuracoes_globais"]["epub"]["css_global"]
        for seletor, propriedades in css_global.items():
            css_lines.append(f"{seletor} {{")
            for prop, valor in propriedades.items():
                css_lines.append(f"  {prop}: {valor};")
            css_lines.append("}")
            css_lines.append("")

        for nome_estilo, config in self.estilos.items():
            epub_config = config["epub"]
            seletor = epub_config["seletor"]
            propriedades = epub_config["propriedades"]

            css_lines.append(f"/* {nome_estilo} */")
            css_lines.append(f"{seletor} {{")
            for prop, valor in propriedades.items():
                css_lines.append(f"  {prop}: {valor};")
            css_lines.append("}")
            css_lines.append("")

        return "\n".join(css_lines)

    def obter_tag_semantica(self, nome_estilo: str) -> str:
        if nome_estilo not in self.estilos:
            return "p"
        return self.estilos[nome_estilo]["semantica"]["tag_html"]

    def obter_classe_css(self, nome_estilo: str) -> str:
        if nome_estilo not in self.estilos:
            return ""
        return self.estilos[nome_estilo]["epub"]["classe_css"]


def gerar_epub(projeto: str, idioma: str):
    base_dir = Path("projetos") / projeto
    output_path = base_dir / "output" / idioma / "livro_completo.epub"
    config_path = base_dir / "config.json"
    
    # CORREÇÃO: Caminho do estilo_livro.json
    estilos_config_path = base_dir / "estilos" / "estilo_livro.json" 
    
    templates_dir = Path("templates") / "epub" # Caminho para templates do EPUB
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not config_path.exists():
        print(f"❌ Arquivo de configuração não encontrado: {config_path}")
        return

    if not templates_dir.exists():
        print(f"❌ Diretório de templates não encontrado: {templates_dir}")
        return
    
    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    titulo_livro = config.get("titulo", "Livro Digital")
    autor_livro = config.get("autor", "Autor Desconhecido")
    data_pub = config.get("data_publicacao", str(date.today()))

    idioma_cfg = config.get("idioma", idioma)
    if idioma_cfg.lower() == "pt_br":
        idioma_final = "pt-BR"
    elif idioma_cfg.lower() == "en":
        idioma_final = "en-US"
    else:
        idioma_final = idioma_cfg

    css_content = ""
    if estilos_config_path.exists():
        gerenciador_estilos = GerenciadorEstilos(estilos_config_path)
        css_content = gerenciador_estilos.gerar_css_completo()
    else:
        print(f"⚠️ Arquivo de estilos não encontrado em: {estilos_config_path}. Usando CSS fallback.")
        css_content = "body { font-family: sans-serif; line-height: 1.6; margin: 5%; }"

    css_filename_in_epub = "styles.css" # Nome canônico do CSS dentro do EPUB

    # Carrega livro_estruturado.json com o conteúdo processado
    livro_path = base_dir / "gerado_automaticamente" / idioma_final.lower().replace("-", "_") / "livro_estruturado.json"
    if not livro_path.exists():
        print(f"❌ Arquivo livro_estruturado.json não encontrado: {livro_path}")
        return
    livro_data = json.loads(livro_path.read_text(encoding="utf-8"))

    # CORREÇÃO: Caminhos para os HTMLs já gerados
    html_base_dir = base_dir / "gerado_automaticamente" / idioma_final.lower().replace("-", "_") / "html"
    html_capitulos_dir = html_base_dir / "capitulos"
    html_partes_dir = html_base_dir / "partes"

    if not html_capitulos_dir.exists() and not html_partes_dir.exists():
        print(f"❌ Nenhuma pasta HTML de capítulos ou partes encontrada em: {html_base_dir}")
        return

    # Mapear todos os HTMLs existentes por seus títulos para facilitar a busca
    # Isso assume que os títulos no livro_estruturado.json correspondem aos títulos principais nos arquivos HTML
    # e que títulos são únicos o suficiente para identificação.
    all_html_files_map = {}

    for html_file_path in html_partes_dir.glob("*.html"):
        content = html_file_path.read_text(encoding="utf-8")
        # Tentativa de extrair o título do HTML (pode ser ajustado para ser mais robusto se necessário)
        # Assumindo que o título principal está em uma tag <h1>
        import re
        match = re.search(r'<h1[^>]*>(.*?)<\/h1>', content, re.IGNORECASE)
        title_from_html = clean_title_for_output(match.group(1).strip()) if match else html_file_path.stem
        all_html_files_map[("parte", title_from_html)] = (html_file_path, content)

    for html_file_path in html_capitulos_dir.glob("*.html"):
        content = html_file_path.read_text(encoding="utf-8")
        match = re.search(r'<h1[^>]*>(.*?)<\/h1>', content, re.IGNORECASE)
        title_from_html = clean_title_for_output(match.group(1).strip()) if match else html_file_path.stem
        all_html_files_map[("capitulo", title_from_html)] = (html_file_path, content)


    # Listas para acumular dados para o TOC e o EPUB
    partes_para_toc = []
    manifest_items = []
    spine_items = []
    
    manifest_items.append({"id": "css", "href": css_filename_in_epub, "media_type": "text/css"})

    parte_counter = 0
    capitulo_counter = 0

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as epub:
        epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        container_tpl = env.get_template("container.xml.j2")
        epub.writestr("META-INF/container.xml", container_tpl.render())
        epub.writestr(f"OEBPS/{css_filename_in_epub}", css_content.encode("utf-8")) # Escreve o CSS

        # Iterar sobre o conteúdo do livro_estruturado.json para encontrar e incluir os HTMLs
        for item in livro_data.get("conteudo", []):
            if item["tipo"] == "parte":
                parte_counter += 1
                canonical_epub_filename = f"parte_{parte_counter:02d}.xhtml"
                
                item_title_cleaned = clean_title_for_output(item.get("titulo_parte", f"Parte {parte_counter}"))
                html_info = all_html_files_map.get(("parte", item_title_cleaned))

                current_part_toc_entry = {
                    "titulo": item_title_cleaned,
                    "arquivo": canonical_epub_filename,
                    "capitulos": [] # Inicializa a lista de capítulos para esta parte
                }

                if html_info:
                    original_html_path, html_content = html_info
                    epub.writestr(f"OEBPS/{canonical_epub_filename}", html_content.encode("utf-8"))
                    manifest_items.append({"id": f"part{parte_counter:02d}", "href": canonical_epub_filename, "media_type": "application/xhtml+xml"})
                    spine_items.append({"idref": f"part{parte_counter:02d}"})
                else:
                    print(f"⚠️ Aviso: HTML para parte '{item_title_cleaned}' não encontrado no disco. Criando placeholder.")
                    placeholder_content = f"""<?xml version="1.0" encoding="UTF-8"?>
                    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{idioma_final}" lang="{idioma_final}">
                    <head><title>{item_title_cleaned}</title><link rel="stylesheet" href="{css_filename_in_epub}" type="text/css"/></head>
                    <body><section epub:type="part"><h1>{item_title_cleaned}</h1><p>Conteúdo da parte não encontrado.</p></section></body></html>"""
                    epub.writestr(f"OEBPS/{canonical_epub_filename}", placeholder_content.encode("utf-8"))
                    manifest_items.append({"id": f"part{parte_counter:02d}", "href": canonical_epub_filename, "media_type": "application/xhtml+xml"})
                    spine_items.append({"idref": f"part{parte_counter:02d}"})
                
                # Adiciona a parte à lista principal do TOC
                partes_para_toc.append(current_part_toc_entry)

                # --- Início: Processamento de capítulos aninhados dentro desta parte ---
                for nested_chapter_item in item.get("capitulos", []):
                    if nested_chapter_item["tipo"] == "capitulo":
                        capitulo_counter += 1
                        canonical_epub_filename_chap = f"capitulo_{capitulo_counter:02d}.xhtml"
                        
                        chap_title_cleaned = clean_title_for_output(nested_chapter_item.get("titulo1", f"Capítulo {capitulo_counter}"))
                        html_info_chap = all_html_files_map.get(("capitulo", chap_title_cleaned))

                        if html_info_chap:
                            original_html_path_chap, html_content_chap = html_info_chap
                            epub.writestr(f"OEBPS/{canonical_epub_filename_chap}", html_content_chap.encode("utf-8"))

                            manifest_items.append({"id": f"cap{capitulo_counter:02d}", "href": canonical_epub_filename_chap, "media_type": "application/xhtml+xml"})
                            spine_items.append({"idref": f"cap{capitulo_counter:02d}"})
                            
                            current_part_toc_entry["capitulos"].append({ # Adiciona ao 'capitulos' da parte atual
                                "titulo": chap_title_cleaned,
                                "arquivo": canonical_epub_filename_chap
                            })
                        else:
                            print(f"⚠️ Aviso: HTML para capítulo '{chap_title_cleaned}' (aninhado) não encontrado no disco. Criando placeholder.")
                            placeholder_content_chap = f"""<?xml version="1.0" encoding="UTF-8"?>
                            <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{idioma_final}" lang="{idioma_final}">
                            <head><title>{chap_title_cleaned}</title><link rel="stylesheet" href="{css_filename_in_epub}" type="text/css"/></head>
                            <body><section epub:type="chapter"><h1>{chap_title_cleaned}</h1><p>Conteúdo do capítulo aninhado não encontrado.</p></section></body></html>"""
                            epub.writestr(f"OEBPS/{canonical_epub_filename_chap}", placeholder_content_chap.encode("utf-8"))
                            manifest_items.append({"id": f"cap{capitulo_counter:02d}", "href": canonical_epub_filename_chap, "media_type": "application/xhtml+xml"})
                            spine_items.append({"idref": f"cap{capitulo_counter:02d}"})
                            current_part_toc_entry["capitulos"].append({
                                "titulo": chap_title_cleaned,
                                "arquivo": canonical_epub_filename_chap
                            })
                # --- Fim: Processamento de capítulos aninhados ---
            
            elif item["tipo"] == "capitulo": # Este bloco trata capítulos de nível superior (não aninhados em partes)
                capitulo_counter += 1
                canonical_epub_filename = f"capitulo_{capitulo_counter:02d}.xhtml"
                
                item_title_cleaned = clean_title_for_output(item.get("titulo1", f"Capítulo {capitulo_counter}"))
                html_info = all_html_files_map.get(("capitulo", item_title_cleaned))

                if html_info:
                    original_html_path, html_content = html_info
                    epub.writestr(f"OEBPS/{canonical_epub_filename}", html_content.encode("utf-8"))

                    manifest_items.append({"id": f"cap{capitulo_counter:02d}", "href": canonical_epub_filename, "media_type": "application/xhtml+xml"})
                    spine_items.append({"idref": f"cap{capitulo_counter:02d}"})
                    
                    # Adiciona a uma "Parte" genérica de "Capítulos Avulsos" no TOC
                    if not partes_para_toc or partes_para_toc[-1]["titulo"] != "Capítulos Avulsos":
                        partes_para_toc.append({
                            "titulo": "Capítulos Avulsos", 
                            "arquivo": "", # Partes avulsas sem arquivo próprio inicial
                            "capitulos": []
                        })
                    partes_para_toc[-1]["capitulos"].append({
                        "titulo": item_title_cleaned,
                        "arquivo": canonical_epub_filename
                    })
                else:
                    print(f"⚠️ Aviso: HTML para capítulo '{item_title_cleaned}' (avulso) não encontrado no disco. Criando placeholder.")
                    placeholder_content = f"""<?xml version="1.0" encoding="UTF-8"?>
                    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{idioma_final}" lang="{idioma_final}">
                    <head><title>{item_title_cleaned}</title><link rel="stylesheet" href="{css_filename_in_epub}" type="text/css"/></head>
                    <body><section epub:type="chapter"><h1>{item_title_cleaned}</h1><p>Conteúdo do capítulo avulso não encontrado.</p></section></body></html>"""
                    epub.writestr(f"OEBPS/{canonical_epub_filename}", placeholder_content.encode("utf-8"))
                    manifest_items.append({"id": f"cap{capitulo_counter:02d}", "href": canonical_epub_filename, "media_type": "application/xhtml+xml"})
                    spine_items.append({"idref": f"cap{capitulo_counter:02d}"})
                    
                    if not partes_para_toc or partes_para_toc[-1]["titulo"] != "Capítulos Avulsos":
                        partes_para_toc.append({
                            "titulo": "Capítulos Avulsos",
                            "arquivo": "",
                            "capitulos": []
                        })
                    partes_para_toc[-1]["capitulos"].append({
                        "titulo": item_title_cleaned,
                        "arquivo": canonical_epub_filename
                    })


        # Gera indice.xhtml (toc-visual)
        indice_tpl = env.get_template("indice.xhtml.j2")
        indice_content = indice_tpl.render(
            titulo=titulo_livro,
            lang=idioma_final, 
            partes=partes_para_toc, 
            caminho_css=css_filename_in_epub 
        )
        epub.writestr("OEBPS/indice.xhtml", indice_content.encode("utf-8"))
        manifest_items.append({
            "id": "indice",
            "href": "indice.xhtml",
            "media_type": "application/xhtml+xml"
        })
        spine_items.insert(0, {"idref": "indice"}) 


        # Gera nav.xhtml (navigation document)
        nav_tpl = env.get_template("nav.xhtml.j2")
        nav_content = nav_tpl.render(
            titulo=titulo_livro,
            partes=partes_para_toc, 
            lang=idioma_final, 
            caminho_css=css_filename_in_epub 
        )
        epub.writestr("OEBPS/nav.xhtml", nav_content.encode("utf-8"))
        manifest_items.append({
            "id": "nav",
            "href": "nav.xhtml",
            "media_type": "application/xhtml+xml",
            "properties": "nav"
        })
        spine_items.append({"idref": "nav", "linear": "no"})

        opf_tpl = env.get_template("content.opf.j2")
        epub.writestr("OEBPS/content.opf", opf_tpl.render(
            titulo=titulo_livro,
            autor=autor_livro,
            data=data_pub,
            idioma=idioma_final,
            manifest_items=manifest_items,
            spine_items=spine_items,
        ))

    print(f"✅ EPUB gerado com sucesso: {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projeto", required=True)
    parser.add_argument("--idioma", default="pt_br")
    args = parser.parse_args()

    gerar_epub(args.projeto, args.idioma)


if __name__ == "__main__":
    main()
