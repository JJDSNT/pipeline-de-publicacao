# scripts/gerar_manifesto.py
import json
from pathlib import Path
import argparse
import re


def extrair_numero_capitulo(nome_arquivo: str) -> int:
    match = re.match(r"^(\d+)", nome_arquivo)
    return int(match.group(1)) if match else float("inf")


def gerar_manifesto(raiz_projeto: Path, idioma: str):
    config_path = raiz_projeto / "config.json"
    if not config_path.exists():
        print(f"❌ Arquivo não encontrado: {config_path}")
        return

    config = json.loads(config_path.read_text(encoding="utf-8"))
    ordem_predefinida = config.get("ordem_predefinida", [])
    mapeamento_partes = {
        int(k): int(v) for k, v in config.get("mapeamento_partes", {}).items()
    }

    # DEBUG: Mostrar configuração
    print(f"📋 Ordem predefinida: {ordem_predefinida}")
    print(f"📋 Mapeamento partes: {mapeamento_partes}")

    base_input = raiz_projeto / "input" / idioma
    capitulos_dir = base_input / "capitulos"

    # DEBUG: Verificar se a pasta existe
    print(f"📁 Pasta capítulos: {capitulos_dir}")
    print(f"📁 Pasta existe: {capitulos_dir.exists()}")

    if capitulos_dir.exists():
        arquivos_odt = list(capitulos_dir.glob("*.odt"))
        print(f"📄 Arquivos .odt encontrados: {[f.name for f in arquivos_odt]}")
    else:
        print("❌ Pasta de capítulos não existe!")
        return

    capitulos = sorted(
        [f.stem for f in capitulos_dir.glob("*.odt")],
        key=extrair_numero_capitulo
    )

    # DEBUG: Mostrar capítulos encontrados
    print(f"📚 Capítulos ordenados: {capitulos}")

    capitulo_para_parte = {
        v: f"{k} parte" for k, v in mapeamento_partes.items()
    }

    # DEBUG: Mostrar mapeamento
    print(f"🗂️ Capítulo para parte: {capitulo_para_parte}")

    ordem_final = []
    for item in ordem_predefinida:
        print(f"🔄 Processando item: {item}")
        if item == "PARTES":
            print("   → Adicionando capítulos e partes...")
            for cap in capitulos:
                numero = extrair_numero_capitulo(cap)
                parte = capitulo_para_parte.get(numero)
                print(f"   → Capítulo {cap} (num: {numero}) → Parte: {parte}")
                if parte and parte not in ordem_final:
                    ordem_final.append(parte)
                    print(f"     ✅ Adicionada parte: {parte}")
                ordem_final.append(cap)
                print(f"     ✅ Adicionado capítulo: {cap}")
        else:
            ordem_final.append(item)
            print(f"   ✅ Adicionado item: {item}")

    # DEBUG: Mostrar ordem final
    print(f"📋 Ordem final: {ordem_final}")

    manifesto = {
        "modelo_llm": config.get("modelo_llm"),
        "tamanho_max_prompt": config.get("tamanho_max_prompt"),
        "estilos": str(Path(config.get("estilos")).as_posix()),
        "formato": config.get("formato"),
        "capa_epub": str(Path("input") / idioma / "images" / "cover.jpg"),
        "ordem": ordem_final
    }

    manifest_path = raiz_projeto / "gerado_automaticamente" / idioma / "manifesto.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifesto, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"✅ Manifesto gerado: {manifest_path.resolve().relative_to(Path.cwd())}")


def main():
    parser = argparse.ArgumentParser(description="Gerar manifesto com base no config.json")
    parser.add_argument("--projeto", required=True, help="Nome do projeto")
    parser.add_argument("--idioma", default="pt_br", help="Idioma do conteúdo")
    args = parser.parse_args()

    raiz_projeto = Path("projetos") / args.projeto
    gerar_manifesto(raiz_projeto, args.idioma)


if __name__ == "__main__":
    main()