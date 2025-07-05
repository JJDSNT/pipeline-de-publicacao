# path/to/file: scripts/parse_para_json.py

import argparse
import json
from pathlib import Path


def processar_arquivo_md(caminho_md: Path, tipo_forcado: str = None) -> dict:
    linhas = caminho_md.read_text(encoding="utf-8").splitlines()
    linhas = [linha.strip() for linha in linhas if linha.strip() != ""]

    if not linhas:
        raise ValueError(f"Arquivo {caminho_md.name} está vazio.")

    tipos_simples = {"epigrafe", "agradecimentos", "introducao", "posfacio"}
    if tipo_forcado in tipos_simples:
        titulo = linhas[0]
        corpo = linhas[1:] if len(linhas) > 1 else []
        return {
            "tipo": tipo_forcado,
            "titulo": titulo,
            "corpo_do_texto": corpo,
        }

    if len(linhas) < 2:
        raise ValueError(
            f"Arquivo {caminho_md.name} não possui título e subtítulo suficientes."
        )

    titulo1 = linhas[0]
    titulo2 = linhas[1]
    corpo = linhas[2:]

    tipo = tipo_forcado or (
        "parte" if titulo1.lower().startswith("parte") else "capitulo"
    )

    return {
        "tipo": tipo,
        "titulo_parte" if tipo == "parte" else "titulo1": titulo1,
        "subtitulo_parte" if tipo == "parte" else "titulo2": titulo2,
        "corpo_do_texto": corpo,
    }


def processar_diretorio(origem: Path, destino: Path, tipo: str = None) -> None:
    if not origem.exists():
        print(f"⚠️ Diretório não encontrado: {origem}")
        return

    destino.mkdir(parents=True, exist_ok=True)

    for caminho_md in origem.glob("*.md"):
        try:
            tipo_dinamico = tipo
            if tipo == "componente":
                tipo_dinamico = caminho_md.stem.lower()

            estrutura = processar_arquivo_md(
                caminho_md, tipo_forcado=tipo_dinamico
            )

            nome_json = caminho_md.stem + ".json"
            caminho_json = destino / nome_json

            with caminho_json.open("w", encoding="utf-8") as f:
                json.dump(estrutura, f, ensure_ascii=False, indent=2)

            print(
                f"✅ {tipo_dinamico.capitalize()}: "
                f"{caminho_md.name} → {nome_json}"
            )
        except Exception as e:
            print(f"❌ Erro em {caminho_md.name}: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse arquivos .md em JSON estruturado"
    )
    parser.add_argument(
        "--projeto",
        default="liderando_transformacao",
        help="Nome do projeto",
    )
    parser.add_argument(
        "--idioma",
        default="pt_br",
        help="Idioma do conteúdo",
    )
    args = parser.parse_args()

    base = Path(__file__).resolve().parents[1]
    raiz = base / "projetos" / args.projeto / "gerado_automaticamente" / args.idioma

    print()
    print(
        "📦 Convertendo arquivos .md para JSON "
        f"no projeto '{args.projeto}' ({args.idioma})"
    )

    processar_diretorio(
        raiz / "md" / "capitulos",
        raiz / "json" / "capitulos",
        tipo="capitulo",
    )
    processar_diretorio(
        raiz / "md" / "partes",
        raiz / "json" / "partes",
        tipo="parte",
    )
    processar_diretorio(
        raiz / "md" / "componentes",
        raiz / "json" / "componentes",
        tipo="componente",
    )

    print("\n✅ Parsing finalizado.\n")


if __name__ == "__main__":
    main()
