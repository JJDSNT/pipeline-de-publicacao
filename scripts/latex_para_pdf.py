# scripts/latex_para_pdf.py
import argparse
from pathlib import Path
import subprocess
import sys
import os
import time
import shutil
import traceback

def compile_latex_to_pdf(projeto: str, idioma_arg: str, compiler: str):
    """
    Compila o arquivo LaTeX gerado para um PDF usando o compilador especificado.
    O arquivo .tex é lido de 'gerado_automaticamente/<idioma>/tex/'
    e o PDF final é salvo em 'output/<idioma>/', com arquivos auxiliares na pasta .tex.
    """
    start_time = time.time()
    print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(start_time))}] ▶️ Iniciando compilação LaTeX para PDF...")

    base_dir = Path("projetos") / projeto
    
    # --- Normalização do Idioma ---
    if idioma_arg.lower() == "pt-br":
        idioma_normalizado_para_path = "pt-BR"
    elif idioma_arg.lower() == "en":
        idioma_normalizado_para_path = "en-US"
    else:
        idioma_normalizado_para_path = idioma_arg

    # --- CAMINHOS ---
    latex_source_dir = base_dir / "gerado_automaticamente" / idioma_normalizado_para_path / "tex"
    output_pdf_dir = base_dir / "output" / idioma_normalizado_para_path 
    
    output_tex_filename = "livro_completo_para_latex.tex" 
    output_pdf_filename_final = "livro_completo_latex.pdf" 
    output_pdf_filename_temp = "livro_completo_para_latex.pdf" 

    output_tex_path = latex_source_dir / output_tex_filename
    output_pdf_path_final = output_pdf_dir / output_pdf_filename_final
    output_pdf_path_temp = latex_source_dir / output_pdf_filename_temp

    # 1. Verificar se o arquivo .tex existe
    if not output_tex_path.exists():
        print(f"❌ Erro: Arquivo LaTeX NÃO ENCONTRADO para compilação: {output_tex_path.resolve()}")
        print("Certifique-se de que 'python scripts/gerar_latex.py' foi executado e criou este arquivo.")
        return False

    # 2. Garantir que os diretórios existam
    latex_source_dir.mkdir(parents=True, exist_ok=True)
    output_pdf_dir.mkdir(parents=True, exist_ok=True)
    print(f"✅ Diretórios de trabalho confirmados/criados: {latex_source_dir.resolve()} e {output_pdf_dir.resolve()}")

    print(f"\n▶️ Iniciando compilação do PDF para o projeto '{projeto}' ({idioma_arg}) usando '{compiler}'...")

    try:
        # 3. Executar o compilador LaTeX múltiplas vezes
        num_compilations = 2 

        for i in range(1, num_compilations + 1):
            compilation_start_time = time.time()
            print(f"  Executando '{compiler}' (passo {i}/{num_compilations})...")
            
            command = [
                compiler,
                '-interaction=nonstopmode',
                str(output_tex_path.name) 
            ]
            
            # Removidas as mensagens de comando e cwd para subprocess para uma saída mais limpa
            result = subprocess.run(
                command,
                cwd=latex_source_dir, 
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"❌ Erro na compilação LaTeX (passo {i}):")
                print("--- Saída do Compilador (stdout) ---")
                print(result.stdout)
                print("--- Erros (stderr) ---")
                print(result.stderr)
                print(f"A compilação (passo {i}) falhou. Continuaremos, mas o PDF pode estar incompleto ou ausente.")
            else:
                compilation_end_time = time.time()
                print(f"  Compilação (passo {i}) concluída em {compilation_end_time - compilation_start_time:.2f} segundos.")
        
        print(f"\n--- Processamento Pós-compilação: Cópia e Verificação do PDF ---")
        # 4. Copiar o PDF gerado para o diretório final
        print(f"  Verificando existência do PDF TEMPORÁRIO esperado: {output_pdf_path_temp.name}")
        if output_pdf_path_temp.exists():
            print(f"  ✅ PDF TEMPORÁRIO ENCONTRADO em: {output_pdf_path_temp.parent.name}/")
            try:
                if output_pdf_path_final.exists():
                    print(f"  Removendo PDF FINAL existente em {output_pdf_path_final.name} para evitar conflito.")
                    output_pdf_path_final.unlink()
                else:
                    print(f"  Nenhum PDF FINAL existente encontrado em {output_pdf_path_final.name}.")

                print(f"  Copiando '{output_pdf_path_temp.name}' para '{output_pdf_path_final.name}'...")
                shutil.copy(output_pdf_path_temp, output_pdf_path_final)
                print(f"✅ PDF copiado com sucesso para: {output_pdf_path_final.name}")
                
                # VERIFICAÇÃO EXTRA: Confirmar que o arquivo realmente existe após a cópia
                if output_pdf_path_final.exists():
                    print(f"✅ VERIFICADO: O arquivo '{output_pdf_path_final.name}' existe no destino final com tamanho {output_pdf_path_final.stat().st_size} bytes.")
                    return True
                else:
                    print(f"❌ ERRO GRAVE: Apesar da cópia reportar sucesso, o arquivo '{output_pdf_path_final.name}' NÃO foi encontrado no destino final.")
                    print("Por favor, verifique as permissões da pasta de destino e se o sistema de arquivos está sincronizado.")
                    return False

            except Exception as e:
                print(f"❌ Erro crítico ao copiar o PDF: {e}")
                print(f"Verifique as permissões para os diretórios: {latex_source_dir.name} e {output_pdf_dir.name}")
                return False
        else:
            print(f"❌ Erro: O arquivo PDF TEMPORÁRIO '{output_pdf_path_temp.name}' NÃO foi encontrado APÓS AS TENTATIVAS DE COMPILAÇÃO.")
            print("Isso indica que o compilador LaTeX não conseguiu gerar o PDF. Verifique o arquivo .log para erros críticos.")
            return False

        # 5. Manter arquivos auxiliares gerados no diretório do .tex
        print("\n  (Arquivos temporários e auxiliares são mantidos na pasta 'gerado_automaticamente/tex/' conforme solicitado para depuração.)")

    except FileNotFoundError:
        print(f"❌ Erro: Comando '{compiler}' não encontrado.")
        print("Certifique-se de que o sistema LaTeX (Tex Live, MiKTeX) está instalado")
        print(f"e que o comando '{compiler}' está disponível no seu PATH do sistema.")
        return False
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado durante a compilação ou pós-processamento: {e}")
        traceback.print_exc() 
        return False

    finally:
        end_time = time.time()
        print(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}] ✅ Etapa 'Compilar LaTeX para PDF' concluída em {end_time - start_time:.2f} segundos.")


def main():
    parser = argparse.ArgumentParser(description="Compila um arquivo LaTeX (.tex) em um PDF.")
    parser.add_argument("--projeto", required=True, help="Nome do diretório do projeto (ex: liderando_transformacao)")
    parser.add_argument("--idioma", default="pt-BR", help="Idioma do livro (ex: pt-BR, en-US).")
    parser.add_argument("--compiler", default="xelatex", 
                        choices=['pdflatex', 'xelatex', 'lualatex'],
                        help="Compilador LaTeX a ser usado (pdflatex, xelatex, lualatex). Padrão: xelatex.")
    args = parser.parse_args()

    success = compile_latex_to_pdf(args.projeto, args.idioma, args.compiler)
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
