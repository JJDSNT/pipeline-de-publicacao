#  scripts/gerar_epub.py
import argparse
import json
import zipfile
from pathlib import Path
from typing import Dict, Any, List
from datetime import date
import sys
import re

from jinja2 import Environment, FileSystemLoader

script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent
sys.path.insert(0, str(project_root))

from utils.cleaner import clean_title_for_output, clean_content_text
from utils.gerenciador_de_estilos import GerenciadorEstilos


def gerar_epub(projeto: str, idioma_arg: str):
    base_dir = Path("projetos") / projeto
    config_path = base_dir / "config.json"
    estilos_config_path = base_dir / "estilos" / "estilo_livro.json" 
    templates_dir = Path("templates") / "epub"

    # --- Normalização do Idioma para uso interno e caminhos de pasta ---
    # Convertemos o idioma do argumento para o formato padrão do EPUB (ex: pt-BR)
    # e usamos isso para construir os caminhos.
    if idioma_arg.lower() == "pt_br":
        idioma_normalizado_para_path = "pt-BR"
        idioma_final_para_xml = "pt-BR" # Usado no xml:lang e lang
    elif idioma_arg.lower() == "en":
        idioma_normalizado_para_path = "en-US"
        idioma_final_para_xml = "en-US" # Usado no xml:lang e lang
    else:
        # Assumir que qualquer outro idioma passado está no formato correto para pastas e XML
        idioma_normalizado_para_path = idioma_arg 
        idioma_final_para_xml = idioma_arg

    output_path = base_dir / "output" / idioma_normalizado_para_path / "livro_completo.epub"
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

    css_content = ""
    if estilos_config_path.exists():
        gerenciador_estilos = GerenciadorEstilos(estilos_config_path)
        css_content = gerenciador_estilos.gerar_css_completo()
    else:
        print(f"⚠️ Arquivo de estilos não encontrado em: {estilos_config_path}. Usando CSS fallback.")
        css_content = "body { font-family: sans-serif; line-height: 1.6; margin: 5%; }"

    css_filename_in_epub = "styles.css"

    # Carrega livro_estruturado.json do caminho normalizado
    livro_path = base_dir / "gerado_automaticamente" / idioma_normalizado_para_path / "livro_estruturado.json"
    if not livro_path.exists():
        print(f"❌ Arquivo livro_estruturado.json não encontrado: {livro_path}")
        return
    livro_data = json.loads(livro_path.read_text(encoding="utf-8"))

    # Caminhos para os HTMLs já gerados, usando o caminho normalizado
    html_base_dir = base_dir / "gerado_automaticamente" / idioma_normalizado_para_path / "html"
    html_capitulos_dir = html_base_dir / "capitulos"
    html_partes_dir = html_base_dir / "partes"

    if not html_capitulos_dir.exists() and not html_partes_dir.exists():
        print(f"❌ Nenhuma pasta HTML de capítulos ou partes encontrada em: {html_base_dir}")
        return

    all_html_files_map = {}

    for html_file_path in html_partes_dir.glob("*.html"):
        content = html_file_path.read_text(encoding="utf-8")
        match = re.search(r'<h1[^>]*>(.*?)<\/h1>', content, re.IGNORECASE)
        title_from_html = clean_title_for_output(match.group(1).strip()) if match else html_file_path.stem
        all_html_files_map[("parte", title_from_html)] = (html_file_path, content)

    for html_file_path in html_capitulos_dir.glob("*.html"):
        content = html_file_path.read_text(encoding="utf-8")
        match = re.search(r'<h1[^>]*>(.*?)<\/h1>', content, re.IGNORECASE)
        title_from_html = clean_title_for_output(match.group(1).strip()) if match else html_file_path.stem
        all_html_files_map[("capitulo", title_from_html)] = (html_file_path, content)


    partes_para_toc = []
    manifest_items = []
    spine_items = []
    
    parte_counter = 0
    capitulo_counter = 0

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as epub:
        epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        container_tpl = env.get_template("container.xml.j2")
        epub.writestr("META-INF/container.xml", container_tpl.render())
        
        epub.writestr(f"OEBPS/{css_filename_in_epub}", css_content.encode("utf-8")) 
        
        manifest_items.append({"id": "css", "href": css_filename_in_epub, "media_type": "text/css"})


        for item in livro_data.get("conteudo", []):
            if item["tipo"] == "parte":
                parte_counter += 1
                canonical_epub_filename = f"parte_{parte_counter:02d}.xhtml"
                
                item_title_cleaned = clean_title_for_output(item.get("titulo_parte", f"Parte {parte_counter}"))
                html_info = all_html_files_map.get(("parte", item_title_cleaned))

                current_part_toc_entry = {
                    "titulo": item_title_cleaned,
                    "arquivo": canonical_epub_filename,
                    "capitulos": []
                }

                if html_info:
                    original_html_path, html_content = html_info
                    epub.writestr(f"OEBPS/{canonical_epub_filename}", html_content.encode("utf-8"))
                    manifest_items.append({"id": f"part{parte_counter:02d}", "href": canonical_epub_filename, "media_type": "application/xhtml+xml"})
                    spine_items.append({"idref": f"part{parte_counter:02d}"})
                else:
                    print(f"⚠️ Aviso: HTML para parte '{item_title_cleaned}' não encontrado no disco. Criando placeholder.")
                    placeholder_content = f"""<?xml version="1.0" encoding="UTF-8"?>
                    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{idioma_final_para_xml}" lang="{idioma_final_para_xml}">
                    <head><title>{item_title_cleaned}</title><link rel="stylesheet" href="{css_filename_in_epub}" type="text/css"/></head>
                    <body><section epub:type="part"><h1>{item_title_cleaned}</h1><p>Conteúdo da parte não encontrado.</p></section></body></html>"""
                    epub.writestr(f"OEBPS/{canonical_epub_filename}", placeholder_content.encode("utf-8"))
                    manifest_items.append({"id": f"part{parte_counter:02d}", "href": canonical_epub_filename, "media_type": "application/xhtml+xml"})
                    spine_items.append({"idref": f"part{parte_counter:02d}"})
                
                partes_para_toc.append(current_part_toc_entry)

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
                            
                            current_part_toc_entry["capitulos"].append({
                                "titulo": chap_title_cleaned,
                                "arquivo": canonical_epub_filename_chap
                            })
                        else:
                            print(f"⚠️ Aviso: HTML para capítulo '{chap_title_cleaned}' (aninhado) não encontrado no disco. Criando placeholder.")
                            placeholder_content_chap = f"""<?xml version="1.0" encoding="UTF-8"?>
                            <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{idioma_final_para_xml}" lang="{idioma_final_para_xml}">
                            <head><title>{chap_title_cleaned}</title><link rel="stylesheet" href="{css_filename_in_epub}" type="text/css"/></head>
                            <body><section epub:type="chapter"><h1>{chap_title_cleaned}</h1><p>Conteúdo do capítulo aninhado não encontrado.</p></section></body></html>"""
                            epub.writestr(f"OEBPS/{canonical_epub_filename_chap}", placeholder_content_chap.encode("utf-8"))
                            manifest_items.append({"id": f"cap{capitulo_counter:02d}", "href": canonical_epub_filename_chap, "media_type": "application/xhtml+xml"})
                            spine_items.append({"idref": f"cap{capitulo_counter:02d}"})
                            current_part_toc_entry["capitulos"].append({
                                "titulo": chap_title_cleaned,
                                "arquivo": canonical_epub_filename_chap
                            })
            
            elif item["tipo"] == "capitulo":
                capitulo_counter += 1
                canonical_epub_filename = f"capitulo_{capitulo_counter:02d}.xhtml"
                
                item_title_cleaned = clean_title_for_output(item.get("titulo1", f"Capítulo {capitulo_counter}"))
                html_info = all_html_files_map.get(("capitulo", item_title_cleaned))

                if html_info:
                    original_html_path, html_content = html_info
                    epub.writestr(f"OEBPS/{canonical_epub_filename}", html_content.encode("utf-8"))

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
                else:
                    print(f"⚠️ Aviso: HTML para capítulo '{item_title_cleaned}' (avulso) não encontrado no disco. Criando placeholder.")
                    placeholder_content = f"""<?xml version="1.0" encoding="UTF-8"?>
                    <html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{idioma_final_para_xml}" lang="{idioma_final_para_xml}">
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


        indice_tpl = env.get_template("indice.xhtml.j2")
        indice_content = indice_tpl.render(
            titulo=titulo_livro,
            lang=idioma_final_para_xml, 
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


        nav_tpl = env.get_template("nav.xhtml.j2")
        nav_content = nav_tpl.render(
            titulo=titulo_livro,
            partes=partes_para_toc, 
            lang=idioma_final_para_xml, 
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
            idioma=idioma_final_para_xml,
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
