# ... (imports, carregamento, setup_jinja_env) ...

# Exemplo de fluxo principal
def generate_latex_document(styles_data, content_data, env):
    template = env.get_template('document_template.tex.j2')
    # Se você optou por pré-processar, passaria `latex_render_data` aqui:
    # rendered_latex = template.render(styles=styles_data_preprocessed, content=content_data)
    
    # Se você optar por lógica no template, passaria os estilos ODT/CSS diretamente:
    rendered_latex = template.render(styles=styles_data, content=content_data)

    output_filepath = 'output.tex'
    with open(output_filepath, 'w', encoding='utf-8') as f:
        f.write(rendered_latex)
    print(f"Arquivo LaTeX gerado em: {output_filepath}")
    return output_filepath

# Seu script principal
latex_file = generate_latex_document(styles, content, env)