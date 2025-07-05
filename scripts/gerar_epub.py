# scripts/gerar_epub.py
import argparse
import json
from pathlib import Path
from typing import Dict, Any
import zipfile


class GeradorEPUB:
    """Gera EPUB com capítulos separados a partir do JSON estruturado"""

    def __init__(self, config_estilos: Dict[str, Any]):
        self.config = config_estilos
        self.capitulos = []
        self.metadados = {}

    def processar_json_estruturado(self, json_data: Dict[str, Any]):
        capitulo_atual = None

        for item in json_data.get("conteudo", []):
            tipo = item["tipo"]
            texto = item.get("texto")

            if not texto:
                print(f"⚠️ Item com tipo '{tipo}' não contém campo 'texto'. Ignorado.")
                continue

            if tipo == "TITULO_PRINCIPAL":
                if capitulo_atual:
                    self.capitulos.append(capitulo_atual)
                capitulo_atual = {
                    "titulo": texto,
                    "id": f"cap_{len(self.capitulos) + 1:02d}",
                    "arquivo": f"capitulo_{len(self.capitulos) + 1:02d}.xhtml",
                    "conteudo": []
                }

            if capitulo_atual:
                capitulo_atual["conteudo"].append({"tipo": tipo, "texto": texto})

        if capitulo_atual:
            self.capitulos.append(capitulo_atual)

    def gerar_xhtml_capitulo(self, capitulo: Dict[str, Any]) -> str:
        linhas = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<!DOCTYPE html>',
            '<html xmlns="http://www.w3.org/1999/xhtml">',
            '<head>',
            f'    <title>{capitulo["titulo"]}</title>',
            '    <link rel="stylesheet" type="text/css" href="styles.css"/>',
            '</head>',
            '<body>',
            ''
        ]

        for item in capitulo["conteudo"]:
            tipo = item["tipo"]
            texto = item["texto"]

            if tipo in self.config["estilos"]:
                estilo = self.config["estilos"][tipo]
                tag = estilo["semantica"]["tag_html"]
                classe = estilo["epub"]["classe_css"]
                linhas.append(f'    <{tag} class="{classe}">{texto}</{tag}>')
            else:
                linhas.append(f'    <p>{texto}</p>')

        linhas.extend(['', '</body>', '</html>'])
        return '\n'.join(linhas)

    def gerar_css(self) -> str:
        css_lines = []
        css_global = self.config["configuracoes_globais"]["epub"]["css_global"]
        for seletor, props in css_global.items():
            css_lines.append(f"{seletor} {{")
            for prop, val in props.items():
                css_lines.append(f"  {prop}: {val};")
            css_lines.append("}")
            css_lines.append("")

        for nome_estilo, config in self.config["estilos"].items():
            epub_cfg = config["epub"]
            seletor = epub_cfg["seletor"]
            props = epub_cfg["propriedades"]
            css_lines.append(f"/* {nome_estilo} */")
            css_lines.append(f"{seletor} {{")
            for prop, val in props.items():
                css_lines.append(f"  {prop}: {val};")
            css_lines.append("}")
            css_lines.append("")

        return "\n".join(css_lines)

    def gerar_content_opf(self) -> str:
        linhas = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="BookId">',
            '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">',
            '    <dc:identifier id="BookId" opf:scheme="UUID">urn:uuid:12345678-1234-1234-1234-123456789012</dc:identifier>',
            f'    <dc:title>{self.metadados.get("titulo", "Livro Digital")}</dc:title>',
            f'    <dc:creator opf:role="aut">{self.metadados.get("autor", "Autor")}</dc:creator>',
            '    <dc:language>pt-BR</dc:language>',
            f'    <dc:date opf:event="publication">{self.metadados.get("data_publicacao", "2025-01-01")}</dc:date>',
  
            '  </metadata>',
            '  <manifest>',
            '    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
            '    <item id="css" href="styles.css" media-type="text/css"/>'
        ]
        for cap in self.capitulos:
            linhas.append(f'    <item id="{cap["id"]}" href="{cap["arquivo"]}" media-type="application/xhtml+xml"/>')
        linhas.extend(['  </manifest>', '  <spine toc="ncx">'])
        for cap in self.capitulos:
            linhas.append(f'    <itemref idref="{cap["id"]}"/>')
        linhas.extend(['  </spine>', '</package>'])
        return '\n'.join(linhas)

    def gerar_toc_ncx(self) -> str:
        linhas = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">',
            '  <head>',
            '    <meta name="dtb:uid" content="urn:uuid:12345678-1234-1234-1234-123456789012"/>',
            '    <meta name="dtb:depth" content="1"/>',
            '    <meta name="dtb:totalPageCount" content="0"/>',
            '    <meta name="dtb:maxPageNumber" content="0"/>',
            '  </head>',
            f'  <docTitle><text>{self.metadados.get("titulo", "Livro Digital")}</text></docTitle>',
            '  <navMap>'
        ]
        for i, cap in enumerate(self.capitulos, 1):
            linhas.extend([
                f'    <navPoint id="navPoint-{i}" playOrder="{i}">',
                f'      <navLabel><text>{cap["titulo"]}</text></navLabel>',
                f'      <content src="{cap["arquivo"]}"/>',
                '    </navPoint>'
            ])
        linhas.extend(['  </navMap>', '</ncx>'])
        return '\n'.join(linhas)

    def gerar_epub(self, output_path: Path, metadados: Dict[str, str] = None):
        if metadados:
            self.metadados = metadados

        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as epub:
            epub.writestr('mimetype', 'application/epub+zip', zipfile.ZIP_STORED)
            container_xml = '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
    <rootfiles>
        <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
    </rootfiles>
</container>'''
            epub.writestr('META-INF/container.xml', container_xml)
            epub.writestr('OEBPS/styles.css', self.gerar_css())
            epub.writestr('OEBPS/content.opf', self.gerar_content_opf())
            epub.writestr('OEBPS/toc.ncx', self.gerar_toc_ncx())
            for cap in self.capitulos:
                xhtml = self.gerar_xhtml_capitulo(cap)
                epub.writestr(f'OEBPS/{cap["arquivo"]}', xhtml)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projeto", required=True)
    parser.add_argument("--idioma", required=True)
    args = parser.parse_args()

    base = Path("projetos") / args.projeto
    idioma = args.idioma
    config_path = base / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))

    json_path = base / "gerado_automaticamente" / idioma / "livro_estruturado.json"
    estilos_path = base / config["estilos"]
    epub_path = base / "output" / idioma / "livro_completo.epub"
    epub_path.parent.mkdir(parents=True, exist_ok=True)

    if not json_path.exists():
        print(f"❌ Arquivo JSON estruturado não encontrado: {json_path}")
        exit(1)

    json_data = json.loads(json_path.read_text(encoding="utf-8"))
    estilos_data = json.loads(estilos_path.read_text(encoding="utf-8"))

    gerador = GeradorEPUB(estilos_data)
    gerador.processar_json_estruturado(json_data)

    metadados = {
        "titulo": config.get("titulo", "Livro Digital"),
        "autor": config.get("autor", "Autor Desconhecido"),
        "data_publicacao": config.get("data_publicacao", "2025-01-01")
    }

    gerador.gerar_epub(epub_path, metadados)
    print(f"✅ EPUB gerado: {epub_path}")


if __name__ == "__main__":
    main()
