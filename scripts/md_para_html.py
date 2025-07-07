# scripts/md_para_html.py

import argparse
from pathlib import Path
import markdown


def converter_md_para_html(md_path: Path, html_path: Path):
    texto_md = md_path.read_text(encoding="utf-8")
    html = markdown.markdown(
        texto_md,
        extensions=["fenced_code", "tables", "toc", "codehilite"]
    )
    html_path.write_text(html, encoding="utf-8")
    print(f"✅ Gerado: {html_path.resolve().relative_to(Path.cwd())}")


def processar_diretorio(md_dir: Path, html_dir: Path):
    html_dir.mkdir(parents=True, exist_ok=True)
    for md_file in md_dir.glob("*.md"):
        html_file = html_dir / (md_file.stem + ".html")
        converter_md_para_html(md_file, html_file)


def main():
    parser = argparse.ArgumentParser(description="Converter arquivos .md para .html")
    parser.add_argument("--projeto", required=True, help="Nome do projeto")
    parser.add_argument("--idioma", default="pt_br", help="Idioma (pt_br, en, etc)")
    args = parser.parse_args()

    raiz = Path("projetos") / args.projeto
    md_dir = raiz / "gerado_automaticamente" / args.idioma / "md" / "capitulos"
    html_dir = raiz / "gerado_automaticamente" / args.idioma / "html" / "capitulos"

    print(f"🟢 Convertendo arquivos Markdown para HTML: {args.projeto}/{args.idioma}")
    processar_diretorio(md_dir, html_dir)
    print("🏁 Conversão finalizada.")


if __name__ == "__main__":
    main()
