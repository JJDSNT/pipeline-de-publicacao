import json
from pathlib import Path
from typing import Dict, Any


class GerenciadorEstilos:
    """Classe para gerenciar estilos unificados ODT/EPUB"""

    def __init__(self, config_path: Path):
        self.config = self._carregar_config(config_path)
        self.estilos = self.config["estilos"]

    def _carregar_config(self, path: Path) -> Dict[str, Any]:
        """Carrega configuração de estilos do JSON"""
        return json.loads(path.read_text(encoding="utf-8"))

    def obter_estilo_odt(self, nome_estilo: str) -> Dict[str, Any]:
        """Retorna configuração ODT para um estilo específico"""
        if nome_estilo not in self.estilos:
            raise ValueError(f"Estilo '{nome_estilo}' não encontrado")
        return self.estilos[nome_estilo]["odt"]

    def obter_estilo_epub(self, nome_estilo: str) -> Dict[str, Any]:
        """Retorna configuração EPUB para um estilo específico"""
        if nome_estilo not in self.estilos:
            raise ValueError(f"Estilo '{nome_estilo}' não encontrado")
        return self.estilos[nome_estilo]["epub"]

    def gerar_css_completo(self) -> str:
        """Gera CSS completo para EPUB"""
        css_lines = []

        # CSS global
        css_global = self.config["configuracoes_globais"]["epub"]["css_global"]
        for seletor, propriedades in css_global.items():
            css_lines.append(f"{seletor} {{")
            for prop, valor in propriedades.items():
                css_lines.append(f"  {prop}: {valor};")
            css_lines.append("}")
            css_lines.append("")

        # CSS dos estilos específicos
        for nome_estilo, config in self.estilos.items():
            epub_config = config["epub"]
            seletor = epub_config["seletor"]
            propriedades = epub_config["propriedades"]

            css_lines.append(f"/* {nome_estilo} */")
            css_lines.append(f"{seletor} {{")
            for prop, valor in propriedades.items():
                css_lines.append(f"  {prop}: {valor};")
            css_lines.append("}")
            css_lines.append("")

        return "\n".join(css_lines)

    def obter_tag_semantica(self, nome_estilo: str) -> str:
        """Retorna tag HTML semântica para um estilo"""
        if nome_estilo not in self.estilos:
            return "p"  # fallback
        return self.estilos[nome_estilo]["semantica"]["tag_html"]

    def obter_classe_css(self, nome_estilo: str) -> str:
        """Retorna classe CSS para um estilo"""
        if nome_estilo not in self.estilos:
            return ""
        return self.estilos[nome_estilo]["epub"]["classe_css"]


# Exemplo de uso no pipeline
def processar_json_para_odt(json_content: Dict, gerenciador: GerenciadorEstilos) -> str:
    """Converte JSON estruturado para FODT usando estilos ODT"""
    fodt_content = []

    for item in json_content["conteudo"]:
        tipo_estilo = item["tipo"]
        texto = item["texto"]

        # Obter configuração ODT
        config_odt = gerenciador.obter_estilo_odt(tipo_estilo)

        # Gerar XML FODT com os estilos
        fodt_content.append(f'<text:p text:style-name="{config_odt["nome_estilo"]}">')
        fodt_content.append(texto)
        fodt_content.append('</text:p>')

    return "\n".join(fodt_content)


def processar_json_para_epub(json_content: Dict, gerenciador: GerenciadorEstilos) -> str:
    """Converte JSON estruturado para HTML usando estilos EPUB"""
    html_content = []

    for item in json_content["conteudo"]:
        tipo_estilo = item["tipo"]
        texto = item["texto"]

        # Obter configuração EPUB
        tag_html = gerenciador.obter_tag_semantica(tipo_estilo)
        classe_css = gerenciador.obter_classe_css(tipo_estilo)

        # Gerar HTML com as classes CSS
        html_content.append(f'<{tag_html} class="{classe_css}">')
        html_content.append(texto)
        html_content.append(f'</{tag_html}>')

    return "\n".join(html_content)


# Exemplo de uso prático
if __name__ == "__main__":
    # Simular dados do JSON estruturado
    json_exemplo = {
        "conteudo": [
            {"tipo": "TITULO_PRINCIPAL", "texto": "Liderando a Transformação Digital"},
            {"tipo": "CORPO_TEXTO", "texto": "A transformação digital não é apenas sobre tecnologia..."},
            {"tipo": "SUBTITULO", "texto": "Os Pilares da Mudança"},
            {"tipo": "CITACAO", "texto": "A única constante é a mudança - Heráclito"},
            {"tipo": "CORPO_TEXTO", "texto": "Para implementar uma transformação eficaz..."}
        ]
    }

    # Carregar gerenciador de estilos
    gerenciador = GerenciadorEstilos(Path("estilos_config.json"))

    # Gerar conteúdo para ODT
    conteudo_odt = processar_json_para_odt(json_exemplo, gerenciador)
    print("=== CONTEÚDO ODT ===")
    print(conteudo_odt)

    print("\n" + "="*50 + "\n")

    # Gerar conteúdo para EPUB
    conteudo_html = processar_json_para_epub(json_exemplo, gerenciador)
    print("=== CONTEÚDO HTML (EPUB) ===")
    print(conteudo_html)

    print("\n" + "="*50 + "\n")

    # Gerar CSS completo
    css_completo = gerenciador.gerar_css_completo()
    print("=== CSS COMPLETO ===")
    print(css_completo)
