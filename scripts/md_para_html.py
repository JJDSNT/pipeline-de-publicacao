# scripts/md_para_html.py

import argparse
from pathlib import Path
import markdown
from jinja2 import Environment, FileSystemLoader


def extrair_titulo_do_md(md_path: Path) -> str:
    for linha in md_path.read_text(encoding="utf-8").splitlines():
        if linha.startswith("# "):
            return linha.lstrip("# ").strip()
    return md_path.stem.replace("-", " ").title()


def converter_md_para_html(md_path: Path, html_path: Path, lang: str, template_env, template_nome: str):
    texto_md = md_path.read_text(encoding="utf-8")
    corpo_html = markdown.markdown(
        texto_md,
        extensions=["fenced_code", "tables", "toc", "codehilite"]
    )

    titulo = extrair_titulo_do_md(md_path)
    template = template_env.get_template(template_nome)

    html_renderizado = template.render(
        lang=lang,
        titulo=titulo,
        corpo=corpo_html,
        caminho_css="styles.css"
    )

    html_path.write_text(html_renderizado, encoding="utf-8")
    print(f"✅ Gerado: {html_path.resolve().relative_to(Path.cwd())}")


def processar_diretorio(md_dir: Path, html_dir: Path, lang: str, template_env, template_nome: str):
    html_dir.mkdir(parents=True, exist_ok=True)
    for md_file in md_dir.glob("*.md"):
        html_file = html_dir / (md_file.stem + ".html")
        converter_md_para_html(md_file, html_file, lang, template_env, template_nome)


def main():
    parser = argparse.ArgumentParser(description="Converter arquivos .md para .html com template Jinja2")
    parser.add_argument("--projeto", required=True, help="Nome do projeto")
    parser.add_argument("--idioma", default="pt_br", help="Idioma (pt_br, en, etc)")
    args = parser.parse_args()

    raiz = Path("projetos") / args.projeto
    md_base = raiz / "gerado_automaticamente" / args.idioma / "md"
    html_base = raiz / "gerado_automaticamente" / args.idioma / "html"

    template_dir = raiz / "templates"
    env = Environment(loader=FileSystemLoader(str(template_dir)))

    print(f"🟢 Convertendo arquivos Markdown para HTML: {args.projeto}/{args.idioma}")

    # Capítulos
    processar_diretorio(
        md_dir=md_base / "capitulos",
        html_dir=html_base / "capitulos",
        lang=args.idioma.replace("_", "-"),
        template_env=env,
        template_nome="base_capitulo.html.j2"
    )

    # Partes
    processar_diretorio(
        md_dir=md_base / "partes",
        html_dir=html_base / "partes",
        lang=args.idioma.replace("_", "-"),
        template_env=env,
        template_nome="base_parte.html.j2"
    )

    print("🏁 Conversão finalizada.")


if __name__ == "__main__":
    main()
