import argparse
from pathlib import Path
import subprocess
import os # Importar os para mudar o diretório de trabalho
import sys # Para sys.exit caso pdflatex não seja encontrado

def compile_latex_to_pdf(projeto: str, idioma_arg: str):
    """
    Compila o arquivo LaTeX gerado para um PDF.
    Espera que o arquivo .tex já esteja na pasta output/<idioma>.
    """
    base_dir = Path("projetos") / projeto
    
    # --- Normalização do Idioma (Importante manter em sincronia com gerar_latex.py) ---
    if idioma_arg.lower() == "pt-br":
        idioma_normalizado_para_path = "pt-BR"
    elif idioma_arg.lower() == "en":
        idioma_normalizado_para_path = "en-US"
    else:
        # Fallback para o caso de um idioma não explicitamente mapeado
        idioma_normalizado_para_path = idioma_arg
    
    output_dir = base_dir / "output" / idioma_normalizado_para_path
    output_tex_filename = "livro_completo.tex"
    output_pdf_filename = "livro_completo.pdf"
    
    output_tex_path = output_dir / output_tex_filename
    output_pdf_path = output_dir / output_pdf_filename

    # 1. Verificar se o arquivo .tex existe
    if not output_tex_path.exists():
        print(f"❌ Erro: Arquivo LaTeX não encontrado para compilação: {output_tex_path}")
        print("Certifique-se de ter executado 'python scripts/gerar_latex.py' primeiro.")
        return

    print(f"▶️ Iniciando compilação do PDF para o projeto '{projeto}' ({idioma_arg})...")
    print(f"  Origem LaTeX: {output_tex_path}")
    print(f"  Destino PDF: {output_pdf_path}")

    # 2. Mudar para o diretório de saída
    # Isso é crucial para que pdflatex crie os arquivos auxiliares (.aux, .log, .toc)
    # no mesmo local do .tex e gere o .pdf corretamente.
    original_cwd = Path.cwd() # Salva o diretório atual para retornar depois
    try:
        print(f"  Mudando para o diretório de trabalho: {output_dir}")
        os.chdir(output_dir)

        # 3. Executar pdflatex múltiplas vezes
        # É comum precisar rodar pdflatex 2 ou 3 vezes para que o sumário (tableofcontents)
        # e referências cruzadas (se houver) sejam gerados corretamente.
        num_compilations = 2 # Pode aumentar para 3 se houver muitas referências

        for i in range(1, num_compilations + 1):
            print(f"  Executando 'pdflatex' (passo {i}/{num_compilations})...")
            # A flag '-interaction=nonstopmode' evita que pdflatex pare e peça input
            # em caso de erros, o que é bom para automação.
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', output_tex_filename],
                capture_output=True, # Captura stdout e stderr
                text=True # Decodifica a saída como texto (UTF-8 por padrão)
            )

            if result.returncode != 0:
                print(f"❌ Erro na compilação LaTeX (passo {i}):")
                print("--- stdout ---")
                print(result.stdout)
                print("--- stderr ---")
                print(result.stderr)
                print(f"A compilação falhou. Verifique os logs acima para detalhes.")
                return # Interrompe se houver erro

        # 4. Verificar se o PDF foi gerado
        if output_pdf_path.exists():
            print(f"✅ PDF gerado com sucesso em: {output_pdf_path}")
        else:
            print(f"❌ Erro: O arquivo PDF não foi encontrado após a compilação em {output_pdf_path}.")
            print("Pode ter havido um erro silencioso do pdflatex ou problema de permissão.")

    except FileNotFoundError:
        print("❌ Erro: Comando 'pdflatex' não encontrado.")
        print("Certifique-se de que um sistema LaTeX (como TeX Live ou MiKTeX) está instalado")
        print("e que o comando 'pdflatex' está disponível no seu PATH do sistema.")
        sys.exit(1) # Sai do script se pdflatex não for encontrado
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado durante a compilação: {e}")
    finally:
        # 5. Voltar para o diretório de trabalho original
        # Isso é importante para que outros scripts ou operações subsequentes
        # não sejam afetados pela mudança de diretório.
        print(f"  Voltando para o diretório original: {original_cwd}")
        os.chdir(original_cwd)


def main():
    parser = argparse.ArgumentParser(description="Compila um arquivo LaTeX (.tex) em um PDF.")
    parser.add_argument("--projeto", required=True, help="Nome do diretório do projeto (ex: liderando_transformacao)")
    parser.add_argument("--idioma", default="pt-BR", help="Idioma do livro (ex: pt-BR, en-US).")
    args = parser.parse_args()

    compile_latex_to_pdf(args.projeto, args.idioma)
    print(f"✅ Etapa concluída: Compilar LaTeX para PDF")


if __name__ == "__main__":
    main()
