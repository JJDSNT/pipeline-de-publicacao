# scripts/build_pipeline.py
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

def log(msg: str, arquivo_log: Path, is_subprocess_output=False):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prefix = "[SUBPROCESS]" if is_subprocess_output else ""
    linha = f"[{timestamp}] {prefix} {msg}"
    print(msg) # Imprime a mensagem original sem o timestamp para o console, para clareza visual
    with arquivo_log.open("a", encoding="utf-8") as f:
        f.write(linha + "\n")

def executar_etapa(nome: str, script: str, args: list[str], log_path: Path) -> bool:
    full_command = ["python", script] + args
    
    # Imprime a mensagem de início da etapa diretamente para o console e loga
    log(f"▶️ Iniciando etapa: {nome}", log_path)

    try:
        process = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Imprime a saída do subprocesso em tempo real e loga
        # Usamos `io.TextIOWrapper` para lidar com a saída do pipe como texto
        with process.stdout as stdout_pipe, process.stderr as stderr_pipe:
            # Loop para ler stdout e stderr de forma semi-síncrona (intercalada)
            # Isso melhora a ordem visual no console
            while True:
                stdout_line = stdout_pipe.readline()
                stderr_line = stderr_pipe.readline()

                if stdout_line:
                    log(stdout_line.strip(), log_path, is_subprocess_output=True)
                if stderr_line:
                    log(stderr_line.strip(), log_path, is_subprocess_output=True)
                
                # Se não houver mais saída de ambos e o processo terminou, saia
                if not stdout_line and not stderr_line and process.poll() is not None:
                    break

        # Espera o processo terminar completamente se ainda não o fez
        process.wait()

        if process.returncode == 0:
            log(f"✅ Etapa concluída: {nome}\n", log_path)
            return True
        else:
            log(f"❌ Falha na etapa: {nome} — código {process.returncode}\n", log_path)
            return False

    except FileNotFoundError:
        log(f"❌ Erro: Comando 'python' ou script '{script}' não encontrado para a etapa {nome}.", log_path)
        log(f"Certifique-se de que Python está no PATH e o script '{script}' existe.", log_path)
        return False
    except Exception as e:
        log(f"❌ Erro inesperado na etapa {nome}: {e}\n", log_path)
        return False

# A função 'limpar_output' foi removida, pois não é responsabilidade do build_pipeline.py

def main():
    parser = argparse.ArgumentParser(description="Executar pipeline completa de publicação")
    parser.add_argument("--projeto", default="liderando_transformacao", help="Nome do projeto")
    parser.add_argument("--idioma", default="pt-BR", help="Idioma do conteúdo")
    args = parser.parse_args()

    raiz = Path(__file__).resolve().parents[1] / "projetos" / args.projeto
    cache_dir = raiz / "cache"
    log_dir = raiz / "logs"
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)

    # MODIFICAÇÃO AQUI: Nome do arquivo de log simplificado para pipeline.log
    log_path = log_dir / "pipeline.log" 
    
    # Limpa o log anterior no início de cada execução
    if log_path.exists():
        log_path.write_text("") 

    print(f"\n🚀 Iniciando pipeline para o projeto '{args.projeto}' ({args.idioma})\n")
    log(f"Log da Pipeline para o projeto '{args.projeto}' ({args.idioma})", log_path)

    etapas = [
        ("Gerar Manifesto", "scripts/gerar_manifesto.py"),
        ("Converter ODT → MD", "scripts/converter_odt_para_md.py"),
        ("Converter MD → JSON", "scripts/parse_para_json.py"),
        ("Gerar Tags e Referências", "scripts/gerar_tags_e_referencia.py"),
        ("Validar Estilos", "scripts/validar_estilos.py"),
        ("Converter MD → HTML", "scripts/md_para_html.py"),
        ("Gerar ePub", "scripts/gerar_epub.py"),
        ("Mapeamento LaTex", "scripts/debug_latex_styles.py"),
        ("Gerar LaTex", "scripts/gerar_latex.py"),
        ("Validar dados tex","scripts/verify_latex_output.py"),
        ("Gerar PDF", "scripts/latex_para_pdf.py"),
        ("Renderizar JSON → FODT", "scripts/renderizar_json_para_fodt.py"),
        ("Exportar FODT → ODT/PDF", "scripts/consolidar_e_exportar_odt_pdf.py"),
        ("Validar ePub", "scripts/validar_epub.py")
    ]

    args_comuns = ["--projeto", args.projeto, "--idioma", args.idioma]
    sucesso = True

    for nome, script in etapas:
        ok = executar_etapa(nome, script, args_comuns, log_path)
        if not ok:
            sucesso = False
            break

    if sucesso:
        log("\n🏁 Pipeline finalizada com sucesso.", log_path)
        print("\n🏁 Pipeline finalizada com sucesso.")
    else:
        log("\n⚠️ Pipeline interrompida por erro. Veja os logs para detalhes.", log_path)
        print("\n⚠️ Pipeline interrompida por erro. Veja os logs para detalhes.")


if __name__ == "__main__":
    main()
