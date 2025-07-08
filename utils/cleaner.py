# utils/cleaner.py
import re

def clean_title_for_output(title_str: str) -> str:
    """
    Remove marcadores Markdown de título (#) e substitui dois ou mais hífens por travessão (—).
    Usado para limpar títulos principais e subtítulos para a saída final.
    """
    # Remove qualquer quantidade de '#' no início da linha, seguida por espaços
    cleaned_title = re.sub(r'^\s*#+\s*', '', title_str)
    # Substitui dois ou mais hífens (--) por um travessão (—)
    cleaned_title = re.sub(r'--+', '—', cleaned_title)
    return cleaned_title.strip() # Remove espaços em branco no início/fim

def clean_content_text(text: str) -> str:
    """
    Substitui dois ou mais hífens por travessão (—), remove backslashes de final de linha e
    remove espaços em branco extras.
    Usado para limpar o corpo do texto.
    """
    cleaned_text = text
    # Substitui dois ou mais hífens (--) por um travessão (—)
    cleaned_text = re.sub(r'--+', '—', cleaned_text)
    # Remove backslashes (\) no final da linha, possivelmente seguidos por espaços
    cleaned_text = re.sub(r'\\+\s*$', '', cleaned_text) # Remove \ e \\ e \s* no final da linha
    return cleaned_text.strip() # Remove espaços em branco no início/fim
