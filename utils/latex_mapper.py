# utils/latex_mapper.py
def map_odt_to_latex_styles(odt_styles):
    latex_styles_data = {
        "preamble_options": {},
        "commands": {},
        "colors": {}
    }

    # Exemplo de mapeamento para parágrafo_default
    if "paragraph_default" in odt_styles:
        p_style = odt_styles["paragraph_default"]
        latex_styles_data["preamble_options"]["documentclass_fontsize"] = p_style.get("font-size", "12pt").replace("pt", "") + "pt"
        latex_styles_data["commands"]["paragraph_indent"] = p_style.get("text-indent", "0cm")
        latex_styles_data["commands"]["paragraph_linespread"] = p_style.get("line-height", "1.0")
        latex_styles_data["commands"]["paragraph_parskip"] = p_style.get("margin-bottom", "0cm")
        # Mapeamento de cor - Cuidado com isso!
        hex_color = p_style.get("color", "#000000")
        latex_styles_data["colors"]["text_default"] = hex_color[1:] # Apenas o valor HEX
        latex_styles_data["commands"]["paragraph_color_name"] = f"text_default" # Nome da cor LaTeX

    # Exemplo de mapeamento para heading_1
    if "heading_1" in odt_styles:
        h1_style = odt_styles["heading_1"]
        latex_styles_data["commands"]["section_fontsize"] = h1_style.get("font-size", "24pt").replace("pt", "") + "pt"
        latex_styles_data["commands"]["section_fontweight"] = "textbf" if h1_style.get("font-weight") == "bold" else "normalfont"
        hex_color_h1 = h1_style.get("color", "#000000")
        latex_styles_data["colors"]["heading1_color"] = hex_color_h1[1:]
        latex_styles_data["commands"]["section_color_name"] = f"heading1_color"
        latex_styles_data["commands"]["section_margin_top"] = h1_style.get("margin-top", "0cm")
        latex_styles_data["commands"]["section_margin_bottom"] = h1_style.get("margin-bottom", "0cm")

    return latex_styles_data

# No seu script principal:
# from latex_mapper import map_odt_to_latex_styles
# latex_render_data = map_odt_to_latex_styles(styles)
# # Renderizar o template passando latex_render_data e content