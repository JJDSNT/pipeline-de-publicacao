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


def processar_diretorio(origem: Path, destino: Path, tipo: str = None) -> list[dict]:
    if not origem.exists():
        print(f"⚠️ Diretório não encontrado: {origem}")
        return []

    destino.mkdir(parents=True, exist_ok=True)
    resultados = []

    for caminho_md in sorted(origem.glob("*.md")):
        try:
            tipo_dinamico = tipo
            if tipo == "componente":
                tipo_dinamico = caminho_md.stem.lower()

            estrutura = processar_arquivo_md(caminho_md, tipo_forcado=tipo_dinamico)
            resultados.append(estrutura)

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

    return resultados


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse arquivos .md em JSON estruturado"
    )
    parser.add_argument("--projeto", default="liderando_transformacao", help="Nome do projeto")
    parser.add_argument("--idioma", default="pt_br", help="Idioma do conteúdo")
    args = parser.parse_args()

    base = Path(__file__).resolve().parents[1]
    raiz = base / "projetos" / args.projeto
    origem_md = raiz / "gerado_automaticamente" / args.idioma / "md"
    destino_json = raiz / "gerado_automaticamente" / args.idioma / "json"
    destino_json.mkdir(parents=True, exist_ok=True)

    print()
    print(f"📦 Convertendo arquivos .md para JSON no projeto '{args.projeto}' ({args.idioma})")

    componentes = processar_diretorio(origem_md / "componentes", destino_json / "componentes", tipo="componente")
    partes = processar_diretorio(origem_md / "partes", destino_json / "partes", tipo="parte")
    capitulos = processar_diretorio(origem_md / "capitulos", destino_json / "capitulos", tipo="capitulo")

    # 🔧 Consolidar em único JSON estruturado
    json_consolidado = {
        "projeto": args.projeto,
        "idioma": args.idioma,
        "conteudo": componentes + partes + capitulos,
    }

    caminho_consolidado = raiz / "gerado_automaticamente" / args.idioma / "livro_estruturado.json"
    caminho_consolidado.write_text(
        json.dumps(json_consolidado, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"\n📘 JSON consolidado salvo em: {caminho_consolidado}")
    print("\n✅ Parsing finalizado.\n")


if __name__ == "__main__":
    main()
