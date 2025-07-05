import argparse
import subprocess
from pathlib import Path
import json
import hashlib
from datetime import datetime
import shutil


def hash_do_arquivo(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def carregar_cache(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def salvar_cache(path: Path, dados: dict):
    path.write_text(json.dumps(dados, indent=2), encoding="utf-8")


def log(msg: str, arquivo_log: Path):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    linha = f"[{timestamp}] {msg}"
    print(linha)
    with arquivo_log.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")


def executar_etapa(nome: str, script: str, args: list[str], log_path: Path) -> bool:
    try:
        log(f"▶️ Iniciando etapa: {nome}", log_path)
        resultado = subprocess.run(["python", script] + args, capture_output=True, text=True)

        if resultado.returncode == 0:
            log(resultado.stdout.strip(), log_path)
            log(f"✅ Etapa concluída: {nome}\n", log_path)
            return True
        else:
            log(resultado.stdout.strip(), log_path)
            log(resultado.stderr.strip(), log_path)
            log(f"❌ Falha na etapa: {nome} — código {resultado.returncode}\n", log_path)
            return False

    except Exception as e:
        log(f"❌ Erro inesperado na etapa {nome}: {e}\n", log_path)
        return False


def limpar_output(raiz: Path, idioma: str, log_path: Path):
    """Remove arquivos desnecessários do output, mantendo apenas os finais"""
    output_dir = raiz / "output"
    output_idioma = output_dir / idioma
    
    # Arquivos que devem ser mantidos
    arquivos_finais = [
        "livro_completo.fodt",
        "livro_completo.odt", 
        "livro_completo.pdf"
    ]
    
    try:
        # Mover arquivos finais da raiz para o diretório do idioma
        for arquivo in arquivos_finais:
            origem = output_dir / arquivo
            destino = output_idioma / arquivo
            if origem.exists():
                output_idioma.mkdir(parents=True, exist_ok=True)
                shutil.move(str(origem), str(destino))
                log(f"📦 Movido: {arquivo} → {idioma}/", log_path)
        
        # Remover arquivos individuais desnecessários
        fodt_individuais = output_idioma / "fodt"
        if fodt_individuais.exists():
            shutil.rmtree(fodt_individuais)
            log(f"🗑️ Removido: {idioma}/fodt/ (arquivos individuais)", log_path)
        
        log("✅ Limpeza do output concluída", log_path)
        
    except Exception as e:
        log(f"⚠️ Erro na limpeza: {e}", log_path)


def main():
    parser = argparse.ArgumentParser(description="Executar pipeline completa de publicação")
    parser.add_argument("--projeto", default="liderando_transformacao", help="Nome do projeto")
    parser.add_argument("--idioma", default="pt_br", help="Idioma do conteúdo")
    args = parser.parse_args()

    raiz = Path(__file__).resolve().parents[1] / "projetos" / args.projeto
    cache_path = raiz / "cache" / f"pipeline_cache_{args.idioma}.json"
    log_path = raiz / "logs" / f"pipeline_{args.idioma}.log"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text("")  # Limpa log anterior

    print(f"\n🚀 Iniciando pipeline para o projeto '{args.projeto}' ({args.idioma})\n")

    etapas = [
        ("Gerar Manifesto", "scripts/gerar_manifesto.py"),
        ("Converter ODT → MD", "scripts/converter_odt_para_md.py"),
        ("Converter MD → JSON", "scripts/parse_para_json.py"),
        ("Gerar Tags e Referências", "scripts/gerar_tags_e_referencia.py"),
        ("Validar Estilos", "scripts/validar_estilos.py"),
        ("Gerar ePub", "scripts/gerar_epub.py"),
        ("Validar ePub", "scripts/validar_epub.py"),
        ("Renderizar JSON → FODT", "scripts/renderizar_json_para_fodt.py"),
        ("Exportar FODT → ODT/PDF", "scripts/consolidar_e_exportar_odt_pdf.py"),
    ]

    args_comuns = ["--projeto", args.projeto, "--idioma", args.idioma]
    sucesso = True

    for nome, script in etapas:
        ok = executar_etapa(nome, script, args_comuns, log_path)
        if not ok:
            sucesso = False
            break

    if sucesso:
        # Limpar e organizar output
        limpar_output(raiz, args.idioma, log_path)
        print("\n🏁 Pipeline finalizada com sucesso.")
    else:
        print("\n⚠️ Pipeline interrompida por erro. Veja os logs para detalhes.")


if __name__ == "__main__":
    main()