import sys
import argparse
import json
import re
from pathlib import Path
import copy # Import copy for deepcopy

# Adiciona o diretório pai ao PYTHONPATH para importar de utils
sys.path.append(str(Path(__file__).resolve().parents[1]))

# Importa as funções de ordenação E as funções de limpeza do novo módulo cleaner
from utils.ordenador import gerar_ordem
from utils.cleaner import clean_title_for_output, clean_content_text


# A função processar_arquivo_md agora aceitará 'tipos_simples_config' como argumento
def processar_arquivo_md(caminho_md: Path, tipos_simples_config: set = None, tipo_forcado: str = None) -> dict:
    linhas = caminho_md.read_text(encoding="utf-8").splitlines()
    linhas = [linha.strip() for linha in linhas if linha.strip() != ""]

    if not linhas:
        raise ValueError(f"Arquivo {caminho_md.name} está vazio.")

    # Garante que tipos_simples_config é um set, mesmo que vazio
    if tipos_simples_config is None:
        tipos_simples_config = set()
    
    # Usa a lista de tipos simples passada como argumento
    if tipo_forcado in tipos_simples_config:
        titulo = linhas[0]
        corpo = linhas[1:] if len(linhas) > 1 else []
        return {
            "tipo": tipo_forcado,
            "titulo": titulo, # Manter o título com marcação Markdown para limpeza posterior
            "corpo_do_texto": corpo,
        }

    if len(linhas) < 2:
        raise ValueError(
            f"Arquivo {caminho_md.name} não possui título e subtítulo suficientes."
        )

    titulo1 = linhas[0] # Manter o título com marcação Markdown para limpeza posterior
    titulo2 = linhas[1] # Manter o subtítulo com marcação Markdown para limpeza posterior
    corpo = linhas[2:]

    tipo = tipo_forcado or (
        "parte" if titulo1.lower().startswith("# parte") else "capitulo"
    )

    return {
        "tipo": tipo,
        "titulo_parte" if tipo == "parte" else "titulo1": titulo1,
        "subtitulo_parte" if tipo == "parte" else "titulo2": titulo2,
        "corpo_do_texto": corpo,
    }


# A função processar_diretorio agora aceitará 'tipos_simples_config' como argumento
def processar_diretorio(origem: Path, destino: Path, tipos_simples_config: set, tipo: str = None) -> list[dict]:
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

            # Passa a lista de tipos simples para a função processar_arquivo_md
            estrutura = processar_arquivo_md(caminho_md, tipos_simples_config=tipos_simples_config, tipo_forcado=tipo_dinamico)
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

    print(f"📦 Convertendo arquivos .md para JSON no projeto '{args.projeto}' ({args.idioma})\n")

    config_path = raiz / "config.json"
    if not config_path.exists():
        print(f"❌ Erro: Arquivo de configuração '{config_path}' não encontrado.")
        sys.exit(1) # Sai com erro se o config não existir

    config = json.loads(config_path.read_text(encoding="utf-8"))
    
    # Lê os tipos simples do config.json e converte para set para busca rápida
    tipos_simples_do_config = set(config.get("tipos_simples", [])) 
    
    # Passa a lista de tipos simples para as funções processar_diretorio
    componentes = processar_diretorio(origem_md / "componentes", destino_json / "componentes", tipos_simples_do_config, tipo="componente")
    partes = processar_diretorio(origem_md / "partes", destino_json / "partes", tipos_simples_do_config, tipo="parte")
    capitulos = processar_diretorio(origem_md / "capitulos", destino_json / "capitulos", tipos_simples_do_config, tipo="capitulo")

    # Consolidar e ordenar
    todos_blocos_disponiveis = componentes + partes + capitulos
    
    # Dicionário para buscar os blocos JSON pelo seu TÍTULO LIMPO (sem '# ')
    blocos_por_titulo_limpo = {}
    
    # Lista de todos os títulos ORIGINAIS (com '# ') para passar para o ordenador
    titulos_originais_para_ordenador = []


    for bloco in todos_blocos_disponiveis:
        titulo_original_do_bloco = "" 

        if bloco["tipo"] == "parte":
            titulo_original_do_bloco = bloco["titulo_parte"]
        elif bloco["tipo"] == "capitulo":
            titulo_original_do_bloco = bloco["titulo1"]
        elif bloco["tipo"] in tipos_simples_do_config and "titulo" in bloco:
            titulo_original_do_bloco = bloco["titulo"]
        
        if titulo_original_do_bloco:
            titulos_originais_para_ordenador.append(titulo_original_do_bloco)

            # Criar uma cópia profunda para não modificar o bloco original na lista 'todos_blocos_disponiveis'
            bloco_para_consolidado = copy.deepcopy(bloco)

            # Aplica a limpeza a subtítulos/título2 e corpo do texto usando as funções do cleaner.py
            if bloco_para_consolidado["tipo"] == "parte":
                bloco_para_consolidado["subtitulo_parte"] = clean_title_for_output(bloco_para_consolidado["subtitulo_parte"])
            elif bloco_para_consolidado["tipo"] == "capitulo":
                bloco_para_consolidado["titulo2"] = clean_title_for_output(bloco_para_consolidado["titulo2"])
            
            if "corpo_do_texto" in bloco_para_consolidado and isinstance(bloco_para_consolidado["corpo_do_texto"], list):
                bloco_para_consolidado["corpo_do_texto"] = [clean_content_text(line) for line in bloco_para_consolidado["corpo_do_texto"]]
            
            # A chave do dicionário é o título limpo, usando a função de limpeza do cleaner para consistência
            key_for_map = clean_title_for_output(titulo_original_do_bloco)
            blocos_por_titulo_limpo[key_for_map] = bloco_para_consolidado

    # Esta chamada agora retorna os títulos JÁ LIMPIS (sem #, com travessão)
    ordem_desejada_titulos_limpos = gerar_ordem(config, titulos_originais_para_ordenador)
    
    conteudo_ordenado = []
    for titulo_limpo_na_ordem in ordem_desejada_titulos_limpos:
        if titulo_limpo_na_ordem in blocos_por_titulo_limpo:
            bloco_final = blocos_por_titulo_limpo[titulo_limpo_na_ordem]
            
            # Preenche os campos de título principal com a versão já limpa retornada por gerar_ordem
            if bloco_final["tipo"] == "parte":
                bloco_final["titulo_parte"] = titulo_limpo_na_ordem
            elif bloco_final["tipo"] == "capitulo":
                bloco_final["titulo1"] = titulo_limpo_na_ordem
            elif bloco_final["tipo"] in tipos_simples_do_config and "titulo" in bloco_final:
                bloco_final["titulo"] = titulo_limpo_na_ordem
            
            conteudo_ordenado.append(bloco_final)
        else:
            print(f"⚠️ Aviso: Título '{titulo_limpo_na_ordem}' na ordem desejada não encontrado nos blocos processados. "
                      f"Verifique se o título no config.json ou Markdown corresponde exatamente.")
    
    json_consolidado = {
        "projeto": args.projeto,
        "idioma": args.idioma,
        "conteudo": conteudo_ordenado,
    }

    caminho_consolidado = raiz / "gerado_automaticamente" / args.idioma / "livro_estruturado.json"
    caminho_consolidado.write_text(
        json.dumps(json_consolidado, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"\n📘 JSON consolidado salvo em: {caminho_consolidado.relative_to(Path.cwd())}")
    print("\n✅ Parsing finalizado.\n")


if __name__ == "__main__":
    main()
