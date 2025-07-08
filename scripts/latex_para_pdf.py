import subprocess

# ... (funções anteriores) ...

def compile_latex_to_pdf(latex_filepath, compiler='xelatex'): # Use xelatex se for usar fontspec
    try:
        # Comando para compilar. -interaction=nonstopmode evita que o latex pare em erros
        # -output-directory para colocar o PDF no lugar certo
        subprocess.run(
            [compiler, "-interaction=nonstopmode", "-output-directory=output", latex_filepath],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"PDF gerado com sucesso para {latex_filepath}!")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao compilar LaTeX: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        # Pode ser útil salvar os logs do LaTeX também
        print("Verifique os arquivos .log gerados para mais detalhes.")
    except FileNotFoundError:
        print(f"Erro: Compilador '{compiler}' não encontrado. Certifique-se de que LaTeX está instalado e no PATH.")

# Seu script principal, no final
# Certifique-se de que o diretório 'output' existe
import os
os.makedirs('output', exist_ok=True)
compile_latex_to_pdf(latex_file) # Chama o compilador