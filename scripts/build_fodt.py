# path/to/file: scripts/build_pipeline.py

import argparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
import json


def renderizar_template(template_path: Path, dados: dict, destino: Path):
    env = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=False,
    )
    template = env.get_template(template_path.name)
    conteudo = template.render(**dados)
    destino.write_text(conteudo, encoding="utf-8")
    print(f"📝 Gerado: {destino.name}")


def processar_jsons(origem: Path, destino: Path, template_path: Path):
    destino.mkdir(parents=True, exist_ok=True)

    for arquivo_json in origem.glob("*.json"):
        with arquivo_json.open(encoding="utf-8") as f:
            dados = json.load(f)

        nome_saida = arquivo_json.stem + ".fodt"
        caminho_saida = destino / nome_saida
        renderizar_template(template_path, dados, caminho_saida)


def main():
    parser = argparse.ArgumentParser(description="Renderizar FODT a partir de JSON")
    parser.add_argument("--projeto", default="liderando_transformacao", help="Nome do projeto")
    parser.add_argument("--idioma", default="pt_br", help="Idioma do conteúdo")
    args = parser.parse_args()

    raiz = Path(__file__).resolve().parents[1] / "projetos" / args.projeto
    base_json = raiz / "gerado_automaticamente" / args.idioma / "json"
    base_saida = raiz / "gerado_automaticamente" / args.idioma / "fodt"
    base_templates = raiz / "templates"

    print(f"\n🚀 Renderizando templates para o projeto '{args.projeto}' ({args.idioma})")

    processar_jsons(
        base_json / "capitulos",
        base_saida / "capitulos",
        base_templates / "capitulo.fodt.j2",
    )

    processar_jsons(
        base_json / "partes",
        base_saida / "partes",
        base_templates / "parte.fodt.j2",
    )

    print("\n✅ Renderização concluída.\n")


if __name__ == "__main__":
    main()
