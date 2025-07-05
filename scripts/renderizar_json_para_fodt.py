import argparse
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def carregar_estilos(projeto_dir: Path) -> dict:
    """Carrega os estilos personalizados do projeto"""
    arquivo_estilos = projeto_dir / "estilos.json"
    if arquivo_estilos.exists():
        with arquivo_estilos.open("r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def gerar_secao_estilos_xml(estilos: dict) -> str:
    """Gera a seção completa de estilos XML para o documento FODT"""
    xml_estilos = []
    
    for chave_estilo, config in estilos.items():
        odt_config = config.get("odt", {})
        nome_estilo = odt_config.get("nome_estilo", chave_estilo)
        fonte = odt_config.get("fonte", "Liberation Serif")
        tamanho = odt_config.get("tamanho", "12pt")
        cor = odt_config.get("cor", "#000000")
        
        # Propriedades adicionais opcionais
        negrito = 'fo:font-weight="bold"' if odt_config.get("negrito", False) else ''
        italico = 'fo:font-style="italic"' if odt_config.get("italico", False) else ''
        sublinhado = 'style:text-underline-style="solid"' if odt_config.get("sublinhado", False) else ''
        
        # Alinhamento
        alinhamento = odt_config.get("alinhamento", "left")
        align_attr = f'fo:text-align="{alinhamento}"' if alinhamento != "left" else ''
        
        # Espaçamento
        margem_top = odt_config.get("margem_superior", "0pt")
        margem_bottom = odt_config.get("margem_inferior", "0pt")
        
        estilo_xml = f'''
    <style:style style:name="{nome_estilo}" style:family="paragraph">
        <style:paragraph-properties 
            fo:margin-top="{margem_top}"
            fo:margin-bottom="{margem_bottom}"
            {align_attr}/>
        <style:text-properties 
            style:font-name="{fonte}" 
            fo:font-size="{tamanho}"
            fo:color="{cor}"
            {negrito}
            {italico}
            {sublinhado}/>
    </style:style>'''
        
        xml_estilos.append(estilo_xml)
    
    return "\n".join(xml_estilos)


def processar_conteudo_com_estilos(conteudo: str, estilos: dict) -> str:
    """Processa o conteúdo aplicando estilos baseados em marcadores"""
    if not conteudo:
        return ""
    
    linhas = conteudo.split('\n')
    resultado = []
    
    for linha in linhas:
        linha_processada = linha.strip()
        if not linha_processada:
            continue
            
        # Identifica o tipo de conteúdo e aplica o estilo correspondente
        if linha_processada.startswith('# '):
            # Título nível 1
            texto = linha_processada[2:].strip()
            estilo = estilos.get('TITULO1', {}).get('odt', {}).get('nome_estilo', 'Título Principal')
            resultado.append(f'<text:h text:style-name="{estilo}" text:outline-level="1">{texto}</text:h>')
            
        elif linha_processada.startswith('## '):
            # Título nível 2
            texto = linha_processada[3:].strip()
            estilo = estilos.get('TITULO2', {}).get('odt', {}).get('nome_estilo', 'Subtítulo')
            resultado.append(f'<text:h text:style-name="{estilo}" text:outline-level="2">{texto}</text:h>')
            
        elif linha_processada.startswith('### '):
            # Título nível 3
            texto = linha_processada[4:].strip()
            estilo = estilos.get('TITULO3', {}).get('odt', {}).get('nome_estilo', 'Título Nível 3')
            resultado.append(f'<text:h text:style-name="{estilo}" text:outline-level="3">{texto}</text:h>')
            
        elif linha_processada.startswith('**') and linha_processada.endswith('**'):
            # Texto em negrito
            texto = linha_processada[2:-2].strip()
            estilo = estilos.get('DESTAQUE', {}).get('odt', {}).get('nome_estilo', 'Texto Destaque')
            resultado.append(f'<text:p text:style-name="{estilo}">{texto}</text:p>')
            
        elif linha_processada.startswith('> '):
            # Citação
            texto = linha_processada[2:].strip()
            estilo = estilos.get('CITACAO', {}).get('odt', {}).get('nome_estilo', 'Citação')
            resultado.append(f'<text:p text:style-name="{estilo}">{texto}</text:p>')
            
        else:
            # Parágrafo normal
            estilo = estilos.get('CORPO_DO_TEXTO', {}).get('odt', {}).get('nome_estilo', 'Texto Corpo')
            resultado.append(f'<text:p text:style-name="{estilo}">{linha_processada}</text:p>')
    
    return '\n'.join(resultado)


def carregar_jsons(origem: Path) -> list:
    arquivos = sorted(origem.glob("*.json"))
    blocos = []
    for caminho in arquivos:
        with caminho.open("r", encoding="utf-8") as f:
            dados = json.load(f)
            dados["_nome_arquivo"] = caminho.stem
            blocos.append(dados)
    return blocos


def renderizar_para_fodt(blocos: list, template_dir: Path, template_nome: str, 
                        destino: Path, estilos: dict):
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_nome)

    destino.mkdir(parents=True, exist_ok=True)

    # Gera a seção de estilos XML uma única vez
    xml_estilos = gerar_secao_estilos_xml(estilos)

    for bloco in blocos:
        # Processa o conteúdo aplicando estilos dinamicamente
        if "conteudo" in bloco:
            bloco["conteudo_formatado"] = processar_conteudo_com_estilos(bloco["conteudo"], estilos)
        
        # Adiciona contexto para o template
        bloco["xml_estilos"] = xml_estilos
        bloco["estilos_config"] = estilos
        
        # Renderiza o template
        conteudo = template.render(**bloco)
        nome_arquivo = bloco["_nome_arquivo"] + ".fodt"
        caminho_saida = destino / nome_arquivo
        caminho_saida.write_text(conteudo, encoding="utf-8")
        print(f"📄 Gerado: {nome_arquivo}")


def main():
    parser = argparse.ArgumentParser(description="Renderiza arquivos JSON para .fodt com estilos dinâmicos")
    parser.add_argument("--projeto", default="liderando_transformacao", help="Nome do projeto")
    parser.add_argument("--idioma", default="pt_br", help="Idioma do conteúdo")
    args = parser.parse_args()

    base = Path(__file__).resolve().parents[1]
    raiz = base / "projetos" / args.projeto

    # Carrega os estilos personalizados
    estilos = carregar_estilos(raiz)
    
    json_dir = raiz / "gerado_automaticamente" / args.idioma / "json"
    output_dir = raiz / "gerado_automaticamente" / args.idioma / "fodt"
    templates_dir = raiz / "templates"

    print(f"\n🛠️  Gerando .fodt para projeto '{args.projeto}' ({args.idioma})")
    print(f"📎 Estilos carregados: {len(estilos)} estilos personalizados")
    
    if estilos:
        print("🎨 Estilos disponíveis:")
        for chave, config in estilos.items():
            nome = config.get("odt", {}).get("nome_estilo", chave)
            print(f"   • {chave} → {nome}")

    renderizar_para_fodt(
        carregar_jsons(json_dir / "capitulos"),
        templates_dir,
        template_nome="capitulo.fodt.j2",
        destino=output_dir / "capitulos",
        estilos=estilos
    )

    renderizar_para_fodt(
        carregar_jsons(json_dir / "partes"),
        templates_dir,
        template_nome="parte.fodt.j2",
        destino=output_dir / "partes",
        estilos=estilos
    )

    print("\n✅ Arquivos .fodt gerados com estilos dinâmicos aplicados.\n")


if __name__ == "__main__":
    main()