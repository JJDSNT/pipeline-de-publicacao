# path/to/file
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List


def carregar_tags_disponiveis(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"Arquivo de tags_disponiveis.json não encontrado: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("tags_disponiveis", [])


def extrair_tags_do_texto(texto: str) -> List[str]:
    return re.findall(r'\{([A-Z_]+)\}', texto)


def validar_tags_em_arquivo(md_path: Path, tags_validas: List[str]) -> Dict:
    texto = md_path.read_text(encoding="utf-8")
    tags_encontradas = extrair_tags_do_texto(texto)
    tags_unicas = set(tags_encontradas)
    tags_invalidas = sorted(list(tags_unicas - set(tags_validas)))
    return {
        "arquivo": str(md_path),
        "tags_invalidas": tags_invalidas,
        "total_usos": len(tags_encontradas),
        "estatisticas": {tag: tags_encontradas.count(tag) for tag in tags_unicas},
    }


def validar_todos_md(md_dir: Path, tags_validas: List[str]) -> List[Dict]:
    resultados = []
    for md_file in sorted(md_dir.glob("*.md")):
        resultado = validar_tags_em_arquivo(md_file, tags_validas)
        resultados.append(resultado)
    return resultados


def main():
    parser = argparse.ArgumentParser(description="Valida uso de estilos (tags) em arquivos .md")
    parser.add_argument("--projeto", required=True, help="Nome do projeto")
    parser.add_argument("--idioma", required=True, help="Idioma (ex: pt_br)")
    args = parser.parse_args()

    raiz = Path("projetos") / args.projeto
    tags_path = raiz / "gerado_automaticamente" / "tags_disponiveis.json"
    md_dir = raiz / "input" / args.idioma / "capitulos"

    try:
        tags_validas = carregar_tags_disponiveis(tags_path)
    except FileNotFoundError as e:
        print(f"\n❌ {e}\n")
        exit(1)

    resultados = validar_todos_md(md_dir, tags_validas)
    erro = False

    print("\n🔍 VALIDAÇÃO DE ESTILOS EM ARQUIVOS .MD:")
    print("=" * 80)

    for res in resultados:
        if res["tags_invalidas"]:
            erro = True
            print(f"❌ {res['arquivo']} possui tags inválidas: {', '.join(res['tags_invalidas'])}")
        else:
            print(f"✅ {res['arquivo']} - OK")

    print("=" * 80)

    if erro:
        print("\n❌ Validação falhou: existem tags inválidas nos arquivos.")
        exit(1)
    else:
        print("\n✅ Todos os arquivos .md passaram na validação de estilos.")


if __name__ == "__main__":
    main()
