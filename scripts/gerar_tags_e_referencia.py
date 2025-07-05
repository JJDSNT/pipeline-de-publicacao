# scripts/gerar_tags_referencia.py
# path/to/file
import argparse
import json
import re
from pathlib import Path
from typing import Dict, List, Any


class GeradorTagsEstilos:
    """Gera lista de tags disponíveis e valida uso no texto"""

    def __init__(self, config_projeto_path: Path):
        self.config_projeto = self._carregar_config(config_projeto_path)
        self.base_dir = config_projeto_path.parent
        self.config_estilos_path = self.base_dir / self.config_projeto["estilos"]
        self.estilos = self._carregar_config(self.config_estilos_path)["estilos"]
        self.tags_disponiveis = set(self.estilos.keys())

    def _carregar_config(self, path: Path) -> Dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def gerar_lista_tags(self) -> List[str]:
        tags_formatadas = []
        for nome_tag, config in self.estilos.items():
            semantica = config.get("semantica", {})
            odt_config = config.get("odt", {})

            descricao_parts = []
            if odt_config.get("nome_estilo"):
                descricao_parts.append(f'"{odt_config["nome_estilo"]}"')
            if semantica.get("tipo"):
                descricao_parts.append(f"({semantica['tipo'].title()})")
            if semantica.get("tag_html"):
                descricao_parts.append(f"HTML: <{semantica['tag_html']}>")
            if odt_config.get("fonte"):
                descricao_parts.append(f"Font: {odt_config['fonte']}")
            if semantica.get("importancia") and semantica["importancia"] != "normal":
                descricao_parts.append(f"[{semantica['importancia'].upper()}]")

            descricao = " - ".join(descricao_parts) if descricao_parts else "Estilo personalizado"
            tags_formatadas.append(f"{nome_tag} - {descricao}")
        return sorted(tags_formatadas)

    def imprimir_tags_disponiveis(self):
        print("\n🎨 ESTILOS DISPONÍVEIS:")
        print("=" * 80)
        grupos = self._agrupar_por_tipo()
        for tipo, tags in grupos.items():
            if tags:
                print(f"\n📝 {tipo.upper().replace('_', ' ')}:")
                for tag in sorted(tags):
                    odt = self.estilos[tag].get("odt", {})
                    nome = odt.get("nome_estilo", tag)
                    fonte = odt.get("fonte", "")
                    tam = odt.get("tamanho", "")
                    fnt = f" ({fonte}" + (f", {tam}" if tam else "") + ")" if fonte else ""
                    print(f"  • {tag} - {nome}{fnt}")
        print(f"\n📊 Total de estilos disponíveis: {len(self.tags_disponiveis)}")
        print("=" * 80)

    def _agrupar_por_tipo(self) -> Dict[str, List[str]]:
        grupos = {"titulos": [], "paragrafos": [], "listas": [], "destacados": [], "especiais": []}
        for tag, cfg in self.estilos.items():
            tipo = cfg.get("semantica", {}).get("tipo", "")
            html = cfg.get("semantica", {}).get("tag_html", "")
            if tipo == "titulo" or html in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                grupos["titulos"].append(tag)
            elif tipo == "paragrafo" or html == "p":
                grupos["paragrafos"].append(tag)
            elif tipo == "lista" or html in ["li", "ul", "ol"]:
                grupos["listas"].append(tag)
            elif tipo in ["citacao", "codigo", "destaque"]:
                grupos["destacados"].append(tag)
            else:
                grupos["especiais"].append(tag)
        return grupos

    def validar_tags_no_texto(self, texto: str) -> Dict[str, Any]:
        tags_encontradas = re.findall(r'\{([A-Z_]+)\}', texto)
        tags_unicas = set(tags_encontradas)
        return {
            "tags_encontradas": list(tags_unicas),
            "tags_validas": list(tags_unicas & self.tags_disponiveis),
            "tags_invalidas": list(tags_unicas - self.tags_disponiveis),
            "total_usos": len(tags_encontradas),
            "estatisticas": {tag: tags_encontradas.count(tag) for tag in tags_unicas},
        }

    def gerar_arquivo_referencia(self, output_path: Path):
        linhas = [
            "# REFERÊNCIA DE ESTILOS DISPONÍVEIS",
            f"# Gerado automaticamente em {Path(__file__).name}",
            f"# Total de estilos: {len(self.tags_disponiveis)}",
            "",
            "## FORMATO DE USO:",
            "# Use {TAG} e {/TAG} nos arquivos .md",
            "",
            "## ESTILOS DISPONÍVEIS:",
            "",
            "| Tag | Nome no ODT | Tipo | HTML | Fonte | Descrição |",
            "|-----|-------------|------|------|-------|-----------|",
        ]
        for tag in sorted(self.tags_disponiveis):
            cfg = self.estilos[tag]
            odt = cfg.get("odt", {})
            sem = cfg.get("semantica", {})
            desc_parts = []
            if odt.get("negrito"):
                desc_parts.append("Negrito")
            if odt.get("italico"):
                desc_parts.append("Itálico")
            if odt.get("cor") and odt["cor"] != "#000000":
                desc_parts.append(f"Cor: {odt['cor']}")
            descricao = ", ".join(desc_parts)
            linhas.append(
                f"| {tag} | {odt.get('nome_estilo', tag)} | {sem.get('tipo', '')} | {sem.get('tag_html', '')} | {odt.get('fonte', '')} | {descricao} |"
            )
        output_path.write_text("\n".join(linhas), encoding="utf-8")
        print(f"✅ Arquivo de referência gerado: {output_path.resolve().relative_to(Path.cwd())}")


def gerar_referencia_estilos(config_path: Path, projeto: str):
    gerador = GeradorTagsEstilos(config_path)
    gerador.imprimir_tags_disponiveis()

    output_dir_md = Path("output")
    output_dir_md.mkdir(parents=True, exist_ok=True)
    md_path = output_dir_md / "referencia_estilos.md"
    gerador.gerar_arquivo_referencia(md_path)

    tags_json = {
        "tags_disponiveis": list(gerador.tags_disponiveis),
        "total": len(gerador.tags_disponiveis),
        "grupos": gerador._agrupar_por_tipo(),
        "validacao_padrao": r'\{([A-Z_]+)\}.*?\{/\1\}',
    }

    output_json_path = Path("projetos") / projeto / "gerado_automaticamente" / "tags_disponiveis.json"
    output_json_path.parent.mkdir(parents=True, exist_ok=True)
    output_json_path.write_text(json.dumps(tags_json, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"📦 JSON de tags salvo em: {output_json_path.resolve().relative_to(Path.cwd())}")

    return gerador


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gera documentação e JSON com tags de estilo.")
    parser.add_argument("--projeto", required=True, help="Nome do projeto (ex: liderando_transformacao)")
    parser.add_argument("--idioma", required=False, help="Idioma (não usado neste script, incluído por padrão da pipeline)")

    args = parser.parse_args()

    caminho_config = Path("projetos") / args.projeto / "config.json"

    if not caminho_config.exists():
        print(f"❌ Arquivo de configuração não encontrado: {caminho_config}")
        exit(1)

    try:
        gerar_referencia_estilos(caminho_config, args.projeto)
    except Exception as e:
        print(f"❌ Erro durante geração das referências: {e}")
        exit(1)
