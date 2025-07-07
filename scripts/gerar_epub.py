# scripts/gerar_epub.py
import argparse
import json
from pathlib import Path
import zipfile


def gerar_epub(projeto: str, idioma: str):
    base_dir = Path("projetos") / projeto
    html_dir = base_dir / "gerado_automaticamente" / idioma / "html" / "capitulos"
    output_path = base_dir / "output" / idioma / "livro_completo.epub"
    config_path = base_dir / "config.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not html_dir.exists():
        print(f"❌ Pasta com HTMLs não encontrada: {html_dir}")
        return

    if not config_path.exists():
        print(f"❌ Arquivo de configuração não encontrado: {config_path}")
        return

    config = json.loads(config_path.read_text(encoding="utf-8"))
    titulo = config.get("titulo", "Livro Digital")
    autor = config.get("autor", "Autor Desconhecido")
    data_pub = config.get("data_publicacao", "2025-01-01")

    html_files = sorted(html_dir.glob("*.html"))
    if not html_files:
        print("❌ Nenhum HTML encontrado para incluir no EPUB.")
        return

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as epub:
        # Requisitos EPUB
        epub.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        container = '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
        epub.writestr("META-INF/container.xml", container)

        # Gerar estilos básicos
        css = "body { font-family: serif; line-height: 1.6; margin: 5%; }"
        epub.writestr("OEBPS/styles.css", css)

        # Copiar os capítulos
        manifest_items = []
        spine_items = []
        navpoints = []

        for i, html_file in enumerate(html_files, 1):
            id_cap = f"cap{i:02d}"
            nome_saida = f"capitulo_{i:02d}.xhtml"
            html_content = html_file.read_text(encoding="utf-8")

            epub.writestr(f"OEBPS/{nome_saida}", html_content)
            manifest_items.append(f'<item id="{id_cap}" href="{nome_saida}" media-type="application/xhtml+xml"/>')
            spine_items.append(f'<itemref idref="{id_cap}"/>')
            navpoints.append(f'''
      <navPoint id="navPoint-{i}" playOrder="{i}">
        <navLabel><text>Capítulo {i}</text></navLabel>
        <content src="{nome_saida}"/>
      </navPoint>''')

        # Gerar TOC
        toc_ncx = f'''<?xml version="1.0" encoding="UTF-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:12345678-1234-1234-1234-123456789012"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{titulo}</text></docTitle>
  <navMap>
{''.join(navpoints)}
  </navMap>
</ncx>'''
        epub.writestr("OEBPS/toc.ncx", toc_ncx)

        # Gerar content.opf
        content_opf = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="BookId">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:identifier id="BookId">urn:uuid:12345678-1234-1234-1234-123456789012</dc:identifier>
    <dc:title>{titulo}</dc:title>
    <dc:creator opf:role="aut">{autor}</dc:creator>
    <dc:language>pt-BR</dc:language>
    <dc:date>{data_pub}</dc:date>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="css" href="styles.css" media-type="text/css"/>
    {''.join(manifest_items)}
  </manifest>
  <spine toc="ncx">
    {''.join(spine_items)}
  </spine>
</package>'''
        epub.writestr("OEBPS/content.opf", content_opf)

    print(f"✅ EPUB gerado com sucesso: {output_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projeto", required=True)
    parser.add_argument("--idioma", default="pt_br")
    args = parser.parse_args()

    gerar_epub(args.projeto, args.idioma)


if __name__ == "__main__":
    main()
