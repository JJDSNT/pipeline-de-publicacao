# 🚀 Pipeline de Publicação Editorial

> Uma pipeline automatizada, modular e extensível para transformar arquivos `.odt` em publicações profissionais nos formatos `.pdf` e `.epub`, com marcação semântica por LLM, estilos configuráveis, QR codes, validações e suporte completo a workflows com Git e Docker.

---

## 🧩 Parte 1 — Marcação Semântica com LLM

### 🎯 Objetivo

Transformar documentos `.odt` brutos em arquivos de texto `.txt` com **marcações semânticas explícitas** (como `[TITULO1]`, `[CORPO_DO_TEXTO]` etc.), usando **modelos LLM locais via Ollama**.

---

### 📦 Estrutura da Parte 1

```
parte1_marcacao_semantica/
├── scripts/
│   ├── marcar_com_llm.py
│   ├── validar_marcacao.py
│   ├── prompt.py               # Cacheado com @lru_cache
│   ├── tags.py
│   ├── helpers.py              # chunking, fallback, logs
│   └── fallback.py             # Estratégias alternativas se LLM falhar
│
├── entrada/odt/
├── saida/
│   ├── texto_extraido/
│   ├── prompt_gerado/
│   ├── texto_marcado/
│   └── validado/
├── logs/
│   └── erros_validacao.log
├── modelos/phi3_mini/
├── manifest.json
├── testar_pipeline_local.py
└── .gitignore                 # Inclui *.odt, arquivos temporários, etc.
```

---

### 🧠 Funcionalidades Especiais

- ✅ Marcação com tags `[ABRE]...[/FECHA]`
- ✅ Validação dupla: **balanceamento de tags** e **fidelidade ao original**
- ✅ Suporte a **versionamento via Git** dos `.txt` marcados
- ✅ **Cache de prompt** para reduzir latência
- ✅ **Chunking automático** se o texto exceder o tamanho máximo da LLM
- ✅ **Fallback automático** caso a LLM falhe (modelo alternativo, divisão menor, etc.)
- ✅ Pode rodar localmente, em WSL ou via Docker

---

### 🗂 Exemplo de `manifest.json` (Parte 1)

```json
{
  "modelo_llm": "phi3:mini",
  "diretorios": {
    "entrada_odt": "entrada/odt",
    "saida_texto": "saida/texto_extraido",
    "saida_prompt": "saida/prompt_gerado",
    "saida_marcado": "saida/texto_marcado",
    "saida_validado": "saida/validado"
  },
  "tamanho_max_prompt": 12000,
  "validar": true,
  "salvar_invalido": true,
  "usar_fallback": true
}
```

---

## 🎨 Parte 2 — Formatação e Publicação

### 🎯 Objetivo

Aplicar estilos visuais ao conteúdo marcado e exportar nos formatos **PDF** e **EPUB**, com inserção de capa, imagens, QR codes e validação.

---

### 📦 Estrutura da Parte 2

```
parte2_formatacao_publicacao/
├── scripts/
│   ├── aplicar_estilos.py
│   ├── gerar_modelo_odt.py
│   ├── gerar_epub.py            # Usa Calibre CLI
│   ├── gerar_pdf.py
│   ├── gerar_qrcode.py
│   ├── inserir_imagens.py
│   ├── validar_epub.py
│   └── build_pipeline.py
│
├── estilos/
│   ├── odt/
│   └── css/
├── assets/
│   ├── fontes/
│   ├── imagens/
│   └── qr/
├── manuscritos/
│   ├── odt_formatado/
│   ├── formatado_pdf/
│   └── formatado_epub/
├── logs/
├── odt_style_config.json
└── manifest.json
```

---

### 🧷 Manifesto de Publicação

```json
{
  "formato": "A5",
  "modelo_odt": "estilo_claro.odt",
  "estilo_css": "estilo_epub.css",
  "capa_epub": "assets/imagens/capa.jpg",
  "qrcode_linkedin": "https://linkedin.com/in/seunome",
  "inserir_qrcode_em": "sobre_autor.odt",
  "inserir_imagens": {
    "capitulo2.odt": ["assets/imagens/figura1.png"]
  },
  "ordem_capitulos": [
    "falsa_folha_rosto.odt",
    "folha_rosto.odt",
    "introducao.odt",
    "capitulo1.odt"
  ]
}
```

---

## 🐳 Execução com Docker (Opcional)

```bash
docker build -t pipeline-editorial .
docker run --rm -v $(pwd):/app pipeline-editorial python scripts/build_pipeline.py --modo completo
```

---

## 🧪 Execução Manual

```bash
python scripts/marcar_com_llm.py --manifest manifest.json
python scripts/build_pipeline.py --modo completo
```

---

## 📘 Sobre Versionamento

- O conteúdo marcado é armazenado como `.txt`
- Pode ser versionado com Git para rastrear mudanças com diffs precisos
- Ideal para revisão, QA e colaboração

---

## 🛑 Exclusões

- ❌ Não usamos **Pandoc**, pois não há conversão direta de `.odt` → Markdown
- ✅ Preferimos `.txt` com tags + aplicação posterior de estilo `.odt` automatizado

---

## 📚 Disclaimer para o Livro

> Este livro foi produzido com o apoio de ferramentas de inteligência artificial para marcação semântica e formatação, respeitando os direitos autorais e a integridade do conteúdo original. A responsabilidade final pelo conteúdo e revisão é do autor.

---

## 📜 Licença de IA

- Use apenas modelos LLM com permissão de uso **comercial**
- Exemplos compatíveis: `phi3`, `gemma`, `llama`, `mistral`
- Claude MCP: requer análise da licença atual da Anthropic (uso pessoal x comercial)

---

## 💡 Possibilidades Futuras

- Integração com **Claude via MCP**
- Interface Web para validação visual
- Controle de versão visual de revisões por capítulo
- Exportação multilíngue com suporte a múltiplas tipografias
- Uso em uma **editora digital automatizada** ou organização biônica

---

> Com este projeto, você tem uma fundação sólida e extensível para produção editorial de alto nível, com IA e automação desde o manuscrito até a publicação final.
