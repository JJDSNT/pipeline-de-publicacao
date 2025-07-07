# scripts/validar_epub.py
import argparse
import subprocess
from pathlib import Path
import os # Import the os module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--projeto", required=True)
    parser.add_argument("--idioma", required=True)
    args = parser.parse_args()

    epub_path = Path("projetos") / args.projeto / "output" / args.idioma / "livro_completo.epub"

    if not epub_path.exists():
        print(f"❌ Arquivo EPUB não encontrado: {epub_path}")
        exit(1)

    # --- Start of modifications ---
    # Get the absolute path to the pipeline's root directory
    # This assumes 'validar_epub.py' is in 'scripts/' and 'bin/epubcheck-5.2.1/' is at the root
    pipeline_root = Path(__file__).resolve().parent.parent
    epubcheck_jar_path = pipeline_root / "bin" / "epubcheck-5.2.1" / "epubcheck.jar"

    if not epubcheck_jar_path.exists():
        print(f"❌ Arquivo epubcheck.jar não encontrado: {epubcheck_jar_path}")
        print("Certifique-se de que o epubcheck está na pasta 'epubcheck-5.2.1' na raiz do projeto.")
        exit(1)

    print(f"📘 Validando EPUB com epubcheck: {epub_path}")
    # Call Java directly with the full path to the epubcheck.jar
    command = ["java", "-jar", str(epubcheck_jar_path), str(epub_path)]
    result = subprocess.run(command, capture_output=True, text=True)
    # --- End of modifications ---

    if result.returncode == 0:
        print("✅ EPUB válido!")
    else:
        print("❌ Erros encontrados pelo epubcheck:")
        print(result.stdout)
        print(result.stderr)
        exit(1)


if __name__ == "__main__":
    main()
