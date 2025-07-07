import argparse
import json
import zipfile
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def gerar_epub(projeto: str, idioma: str):
    base_dir = Path("projetos") / projeto
    html_dir = base_dir / "gerado_automaticamente" / idioma / "html" / "capitulos"
    output_path = base_dir / "output" / idioma / "livro_completo.epub"
    config_path = base_dir / "config.json"
    templates_dir = Path("templates") / "epub"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not html_dir.exists():
        print(f"❌ Pasta com HTMLs não encontrada: {html_dir}")
        return

    if not config_path.exists():
        print(f"❌ Arquivo de configuração não encontrado: {config_path}")
        return

    env = Environment(loader=FileSystemLoader(templates_dir), autoescape=True)

    config = json.loads(config_path.read_text(encoding="utf-8"))
    titulo = config.get("titulo", "Livro Digital")
    autor = config.get("autor", "Autor Desconhecido")
    data_pub = config.get("data_publicacao", "2025-01-01")

    # Normalização do Idioma para IETF BCP 47 (ex: pt-BR)
    idioma_cfg = config.get("idioma", idioma)
    if idioma_cfg.lower() == "pt_br":
        idioma_final = "pt-BR"
    elif idioma_cfg.lower() == "en":
        idioma_final = "en-US"
    else:
        idioma_final = idioma_cfg

    html_files = sorted(html_dir.glob("*.html"))
    if not html_files:
        print("❌ Nenhum HTML encontrado para incluir no EPUB.")
        return

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as epub:
        epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

        container_tpl = env.get_template("container.xml.j2")
        epub.writestr("META-INF/container.xml", container_tpl.render())

        css_content = "body { font-family: serif; line-height: 1.6; margin: 5%; }"
        epub.writestr("OEBPS/styles.css", css_content.encode("utf-8"))

        manifest_items = []
        spine_items = []
        nav_items_para_nav_xhtml = []  # Para o sumário técnico (nav.xhtml)
        capitulos_para_indice_visual = []  # Para a página de índice visual (indice.xhtml)

        manifest_items.append({"id": "css", "href": "styles.css", "media_type": "text/css"})

        for i, html_file in enumerate(html_files, 1):
            id_cap = f"cap{i:02d}"
            nome_saida = f"capitulo_{i:02d}.xhtml"
            html_content = html_file.read_text(encoding="utf-8")

            epub.writestr(f"OEBPS/{nome_saida}", html_content)
            manifest_items.append({"id": id_cap, "href": nome_saida, "media_type": "application/xhtml+xml"})
            spine_items.append({"idref": id_cap})

            # Popula a lista para o sumário técnico (nav.xhtml)
            nav_items_para_nav_xhtml.append({
                "label": f"Capítulo {i}",
                "src": nome_saida
            })
            # Popula a lista para a página de índice visual (indice.xhtml)
            capitulos_para_indice_visual.append({
                "titulo": f"Capítulo {i}",
                "href": nome_saida
            })

        # --- Gerar a página de Índice/Sumário Visual (indice.xhtml) ---
        # Esta página será o sumário que o leitor verá. Ela é linear.
        indice_tpl = env.get_template("indice.xhtml.j2")
        indice_content = indice_tpl.render(
            titulo=titulo,
            idioma=idioma_final,
            capitulos_para_indice=capitulos_para_indice_visual # Passa os dados para o template
        )
        epub.writestr("OEBPS/indice.xhtml", indice_content)
        manifest_items.append({
            "id": "indice",
            "href": "indice.xhtml",
            "media_type": "application/xhtml+xml"
            # Opcional: properties="rendition:layout-pre-paginated" se for um layout fixo
            # Opcional: properties="nav" se este for o único TOC e não houver nav.xhtml separado (não recomendado para EPUB 3.x)
        })
        # Adicionar o índice no início da spine, como um item linear
        spine_items.insert(0, {"idref": "indice"})


        # --- Gerar o nav.xhtml (o sumário técnico/OCN - OPF Conventional Navigation) ---
        # Este arquivo ainda é necessário e terá a propriedade "nav" no manifest.
        # Ele não precisa ser linkado diretamente no conteúdo visível se o indice.xhtml for o sumário principal.
        nav_tpl = env.get_template("nav.xhtml.j2")
        nav_content = nav_tpl.render(titulo=titulo, nav_items=nav_items_para_nav_xhtml, idioma=idioma_final)
        epub.writestr("OEBPS/nav.xhtml", nav_content)
        
        manifest_items.append({
            "id": "nav",
            "href": "nav.xhtml",
            "media_type": "application/xhtml+xml",
            "properties": "nav"  # Essencial para EPUB 3.x, designa este como o sumário técnico
        })
        spine_items.append({"idref": "nav", "linear": "no"})  # nav.xhtml é non-linear

        # content.opf via template
        opf_tpl = env.get_template("content.opf.j2")
        epub.writestr("OEBPS/content.opf", opf_tpl.render(
            titulo=titulo,
            autor=autor,
            data=data_pub,
            idioma=idioma_final,
            manifest_items=manifest_items,
            spine_items=spine_items,
        ))

    print(f"✅ EPUB gerado com sucesso: {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projeto", required=True)
    parser.add_argument("--idioma", default="pt-BR")
    args = parser.parse_args()

    gerar_epub(args.projeto, args.idioma)


if __name__ == "__main__":
    main()
