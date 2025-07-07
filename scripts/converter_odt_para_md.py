# scripts/converter_odt_para_md.py
import pypandoc
import argparse
from pathlib import Path


def ajustar_titulo_md(caminho_md: Path) -> None:
    conteudo = caminho_md.read_text(encoding="utf-8")
    linhas = conteudo.splitlines()
    novas_linhas = []
    titulos_aplicados = 0

    for linha in linhas:
        if linha.strip() == "":
            novas_linhas.append(linha)
        elif titulos_aplicados == 0:
            novas_linhas.append("# " + linha.strip())
            titulos_aplicados += 1
        elif titulos_aplicados == 1:
            novas_linhas.append("## " + linha.strip())
            titulos_aplicados += 1
        else:
            novas_linhas.append(linha)

    caminho_md.write_text("\n".join(novas_linhas), encoding="utf-8")



def converter_odt_para_md(arquivo_odt: Path, destino_md: Path) -> None:
    print(f"🟡 Convertendo: {arquivo_odt.name} → {destino_md.relative_to(Path.cwd())}")
    pypandoc.convert_file(
        str(arquivo_odt),
        to="markdown",
        outputfile=str(destino_md),
        extra_args=["--wrap=none"],
    )
    ajustar_titulo_md(destino_md)


def processar_diretorio(origem: Path, destino: Path) -> None:
    for arquivo in origem.glob("*.odt"):
        nome_md = arquivo.stem + ".md"
        destino_md = destino / nome_md
        converter_odt_para_md(arquivo, destino_md)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Converter arquivos .odt para .md usando pandoc"
    )
    parser.add_argument(
        "--projeto",
        default="liderando_transformacao",
        help="Nome do projeto",
    )
    parser.add_argument(
        "--idioma",
        default="pt_br",
        help="Idioma do conteúdo (ex: pt_br, en)",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).resolve().parents[1]
    input_dir = base_dir / "projetos" / args.projeto / "input" / args.idioma
    capitulos_dir = input_dir / "capitulos"
    partes_dir = input_dir / "partes"

    output_dir = (
        base_dir
        / "projetos"
        / args.projeto
        / "gerado_automaticamente"
        / args.idioma
    )
    # CORREÇÃO: Usar 'md' como diretório pai, não 'md_capitulos' e 'md_partes'
    md_dir = output_dir / "md"
    md_capitulos = md_dir / "capitulos"
    md_partes = md_dir / "partes"

    md_capitulos.mkdir(parents=True, exist_ok=True)
    md_partes.mkdir(parents=True, exist_ok=True)

    print()
    print(f"🟢 Iniciando conversão no projeto '{args.projeto}' ({args.idioma})")
    processar_diretorio(capitulos_dir, md_capitulos)
    processar_diretorio(partes_dir, md_partes)
    print("✅ Conversão concluída com sucesso.")


if __name__ == "__main__":
    main()
