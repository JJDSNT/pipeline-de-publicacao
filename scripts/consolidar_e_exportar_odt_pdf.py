import json
import subprocess
from pathlib import Path
import argparse
import xml.etree.ElementTree as ET


def consolidar_fodt(raiz_projeto: Path, idioma: str):
    """Consolida arquivos FODT em um único arquivo seguindo a ordem do manifesto"""
    
    # Carregar manifesto
    manifest_path = raiz_projeto / "gerado_automaticamente" / idioma / "manifesto.json"
    if not manifest_path.exists():
        print(f"❌ Manifesto não encontrado: {manifest_path}")
        return False
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        manifesto = json.load(f)
    
    ordem = manifesto.get("ordem", [])
    if not ordem:
        print("❌ Ordem vazia no manifesto")
        return False
    
    print(f"📋 Ordem do manifesto: {ordem}")
    
    # Diretórios de busca
    fodt_dir = raiz_projeto / "gerado_automaticamente" / idioma / "fodt"
    capitulos_dir = fodt_dir / "capitulos"
    partes_dir = fodt_dir / "partes"
    
    print(f"📁 Buscando em: {fodt_dir}")
    print(f"📁 Capítulos: {capitulos_dir}")
    print(f"📁 Partes: {partes_dir}")
    
    # Coletar arquivos FODT na ordem correta
    arquivos_ordenados = []
    
    for item in ordem:
        arquivo_fodt = None
        
        # Buscar em capitulos
        capitulo_path = capitulos_dir / f"{item}.fodt"
        if capitulo_path.exists():
            arquivo_fodt = capitulo_path
            print(f"✅ Encontrado capítulo: {arquivo_fodt}")
        
        # Buscar em partes
        parte_path = partes_dir / f"{item}.fodt"
        if parte_path.exists():
            arquivo_fodt = parte_path
            print(f"✅ Encontrado parte: {arquivo_fodt}")
        
        if arquivo_fodt:
            arquivos_ordenados.append(arquivo_fodt)
        else:
            print(f"⚠️ Arquivo não encontrado: {item}")
    
    if not arquivos_ordenados:
        print("❌ Nenhum arquivo FODT encontrado para consolidar")
        return False
    
    print(f"📚 Arquivos para consolidar: {len(arquivos_ordenados)}")
    
    # Consolidar arquivos
    try:
        # Ler o primeiro arquivo como base
        with open(arquivos_ordenados[0], 'r', encoding='utf-8') as f:
            conteudo_base = f.read()
        
        # Parse XML
        root = ET.fromstring(conteudo_base)
        
        # Encontrar o body
        namespaces = {
            'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
            'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0'
        }
        
        body = root.find('.//office:body/office:text', namespaces)
        if body is None:
            print("❌ Não foi possível encontrar o body do documento")
            return False
        
        # Adicionar conteúdo dos outros arquivos
        for arquivo in arquivos_ordenados[1:]:
            print(f"📄 Adicionando: {arquivo.name}")
            
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Parse do arquivo atual
            arquivo_root = ET.fromstring(conteudo)
            arquivo_body = arquivo_root.find('.//office:body/office:text', namespaces)
            
            if arquivo_body is not None:
                # Adicionar quebra de página
                page_break = ET.Element('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p')
                page_break.set('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}style-name', 'page-break')
                body.append(page_break)
                
                # Adicionar conteúdo
                for elemento in arquivo_body:
                    body.append(elemento)
        
        # Salvar arquivo consolidado
        output_dir = raiz_projeto / "output"
        output_dir.mkdir(exist_ok=True)
        
        arquivo_consolidado = output_dir / "livro_completo.fodt"
        
        # Escrever XML
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ", level=0)
        tree.write(arquivo_consolidado, encoding='utf-8', xml_declaration=True)
        
        print(f"✅ Arquivo consolidado criado: {arquivo_consolidado}")
        
        # Converter para ODT
        try:
            subprocess.run([
                'libreoffice', '--headless', '--convert-to', 'odt', '--outdir', str(output_dir),
                str(arquivo_consolidado)
            ], check=True, capture_output=True)
            print(f"✅ Convertido para ODT: {output_dir / 'livro_completo.odt'}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Erro na conversão para ODT: {e}")
        
        # Converter para PDF
        try:
            subprocess.run([
                'libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', str(output_dir),
                str(arquivo_consolidado)
            ], check=True, capture_output=True)
            print(f"✅ Convertido para PDF: {output_dir / 'livro_completo.pdf'}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Erro na conversão para PDF: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na consolidação: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Consolidar arquivos FODT")
    parser.add_argument("--projeto", required=True, help="Nome do projeto")
    parser.add_argument("--idioma", default="pt_br", help="Idioma do conteúdo")
    args = parser.parse_args()
    
    raiz_projeto = Path("projetos") / args.projeto
    
    print(f"🔧 Consolidando projeto '{args.projeto}' ({args.idioma})")
    sucesso = consolidar_fodt(raiz_projeto, args.idioma)
    
    if sucesso:
        print("✅ Consolidação concluída com sucesso")
    else:
        print("❌ Falha na consolidação")


if __name__ == "__main__":
    main()