# utils/injetor_css.py

def gerar_css_global_com_base_no_metadata(config: dict) -> dict:
    """Gera um CSS global baseado nas fontes e cores do metadata."""
    metadata = config.get("metadata", {})

    serif = metadata.get("fontes_principais_serif", ["Georgia", "serif"])
    sans = metadata.get("fontes_principais_sans_serif", ["Arial", "sans-serif"])
    cor_texto = metadata.get("cores_texto", {}).get("principal", "#333333")

    return {
        "body": {
            "font-family": ", ".join(serif),
            "font-size": "100%",
            "line-height": "1.6",
            "color": cor_texto,
            "margin": "0",
            "padding": "1em"
        },
        "h1, h2, h3, h4, h5, h6": {
            "font-family": ", ".join(sans),
            "margin-top": "1.5em",
            "margin-bottom": "0.8em"
        },
        "p": {
            "margin-bottom": "1em"
        }
    }


def injetar_css_global_se_ausente(config: dict) -> None:
    """Insere css_global no config se não existir, com base no metadata."""
    if "configuracoes_globais" not in config:
        config["configuracoes_globais"] = {}

    if "epub" not in config["configuracoes_globais"]:
        config["configuracoes_globais"]["epub"] = {}

    if "css_global" not in config["configuracoes_globais"]["epub"]:
        config["configuracoes_globais"]["epub"]["css_global"] = gerar_css_global_com_base_no_metadata(config)


def injetar_mapeamento_semantico_se_ausente(config: dict) -> None:
    """Insere mapeamento_semantico padrão se não existir."""
    if "mapeamento_semantico" not in config:
        estilos = config.get("estilos", {})
        nomes_estilos = set(estilos.keys())

        # Heurísticas simples para mapear estilos
        titulos = [e for e in nomes_estilos if "TITULO" in e or "SUBTITULO" in e]
        conteudo = [e for e in nomes_estilos if e in {"CORPO_TEXTO", "CITACAO", "LISTA_ITEM"}]
        especiais = [e for e in nomes_estilos if "CODIGO" in e or "DESTAQUE" in e]

        # Hierarquia padrão
        hierarquia = {
            "nivel_1": titulos[0] if titulos else None,
            "nivel_2": titulos[1] if len(titulos) > 1 else None
        }

        config["mapeamento_semantico"] = {
            "titulos": titulos,
            "conteudo": conteudo,
            "especiais": especiais,
            "hierarquia_navegacao": hierarquia
        }


def injetar_complementos_se_ausentes(config: dict) -> None:
    """
    Garante que o dicionário de configuração contenha as entradas
    css_global e mapeamento_semantico se estiverem ausentes.
    """
    injetar_css_global_se_ausente(config)
    injetar_mapeamento_semantico_se_ausente(config)
