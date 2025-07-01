# 🚀 Pipeline de Publicação Editorial

> Uma pipeline automatizada, modular e extensível para transformar arquivos `.odt` em publicações profissionais nos formatos `.pdf` e `.epub`, com marcação semântica por LLM, estilos configuráveis, cache por hash, paralelismo, validações e suporte completo a workflows com Git e Docker.

---

## ⚙️ Arquitetura Geral

Esta pipeline está organizada em **duas grandes etapas**:

1. **Marcação Semântica com LLM** — conversão `.odt` → `.md`, marcação com IA, validação e parsing para JSON.
2. **Formatação e Publicação** — aplicação de estilos com templates `jinja2` e geração de `.fodt`, `.html`, `.pdf`, `.epub`.

---

## 🧩 Etapa 1 — Marcação Semântica com LLM

### 🎯 Objetivo

Transformar documentos `.odt` em arquivos `.md` com **marcações semânticas explícitas** (`[TITULO1]`, `[CORPO_DO_TEXTO]`, etc.), usando modelos LLM locais via Ollama, com validação e transformação para JSON estruturado.

---

### 📦 Estrutura

```
parte1_marcacao_semantica/
├── scripts/
│   ├── converter_odt_para_md.py
│   ├── marcar_com_llm.py
│   ├── validar_marcacao.py
│   ├── parse_para_json.py
│   ├── prompt.py
│   ├── tags.py
│   ├── helpers.py
│   └── fallback.py
│
├── entrada/odt/
├── gerado_automaticamente/
├── saida/
│   ├── texto_extraido/
│   ├── texto_marcado/
│   ├── validado/
│   └── estruturado_json/
├── cache/
├── logs/
│   └── pipeline.log
├── manifest.json
└── .gitignore
```

---

### 🧠 Funcionalidades

- ✅ Conversão `.odt` → `.md` com `pandoc`
- ✅ Marcação semântica com LLM local (`ollama`)
- ✅ Fallback automático para outro modelo ou chunking
- ✅ Validação:
  - Balanceamento de tags
  - Fidelidade textual
- ✅ Geração de JSON estruturado com `estilo_ref`
- ✅ Suporte a páginas automáticas (capa, créditos, etc.)

---

### ⚙️ Performance e Robustez

- 🔄 **Chunking automático** quando o prompt ultrapassa o limite da LLM
- 🧠 **Cache por hash** (MD5) para reuso de resultados anteriores
- 🧵 **Execução paralela** com `ProcessPoolExecutor`
- 📊 **Logs detalhados** com tempo de execução por etapa e por arquivo

---

## 🎨 Etapa 2 — Formatação e Publicação

### 🎯 Objetivo

Renderizar os arquivos `.json` com `jinja2`, aplicar estilos definidos e gerar `.fodt`, `.html`, `.odt`, `.pdf` e `.epub`.

---

### 📦 Estrutura

```
parte2_formatacao_publicacao/
├── scripts/
│   ├── renderizar_fodt.py
│   ├── renderizar_html.py
│   ├── gerar_css.py
│   ├── build_pipeline.py
│   └── logger.py
│
├── templates/
│   ├── capitulo.fodt.j2
│   ├── capitulo.html.j2
│   ├── pagina_estatica.fodt.j2
│   ├── pagina_estatica.html.j2
│   └── style.css.j2
│
├── estilos/
│   ├── estilos_definicoes.json
│   ├── style.css
│   └── fonts/
│       ├── ArialBlack.ttf
│       ├── LiberationSerif-Regular.ttf
│       └── Georgia-Italic.ttf
│
├── saida/
│   ├── renderizado_odt/
│   ├── renderizado_html/
│   ├── odt_final/
│   ├── pdf_final/
│   └── epub_final/
└── manifest.json
```

---

### 🖋️ Pasta `fonts/` (fontes tipográficas)

- Contém as fontes utilizadas nos estilos declarados
- Usada por LibreOffice na exportação `.odt`/`.pdf` e pode ser incorporada no EPUB
- As fontes podem ser referenciadas no CSS via `@font-face`:

```css
@font-face {
  font-family: "Liberation Serif";
  src: url("../fonts/LiberationSerif-Regular.ttf");
}
```

---

## 📜 Exemplo de Manifesto

```json
{
  "modelo_llm": "phi3:mini",
  "ordem": [
    "capa_falsa",
    "epigrafe",
    "capitulo1",
    "capitulo2",
    "colofao"
  ],
  "estilos": "estilos_definicoes.json",
  "formato": "A5",
  "tamanho_max_prompt": 12000,
  "capa_epub": "assets/imagens/capa.jpg"
}
```

---

## 🎨 Exemplo de `estilos_definicoes.json`

```json
{
  "TITULO1": {
    "odt": {
      "nome_estilo": "Título Principal",
      "fonte": "Arial Black",
      "tamanho": "18pt",
      "cor": "#2C5282"
    },
    "css": {
      "classe": "titulo-principal",
      "propriedades": {
        "font-family": "Arial Black, sans-serif",
        "font-size": "1.8em",
        "color": "#2C5282"
      }
    }
  },
  "CORPO_DO_TEXTO": {
    "odt": {
      "nome_estilo": "Texto Corpo",
      "fonte": "Liberation Serif",
      "tamanho": "12pt"
    },
    "css": {
      "classe": "corpo-texto",
      "propriedades": {
        "font-family": "Georgia, serif",
        "font-size": "1em",
        "text-indent": "2em",
        "line-height": "1.6"
      }
    }
  }
}
```

---

## 🧪 Execução

### Modo local
```bash
python scripts/converter_odt_para_md.py
python scripts/marcar_com_llm.py
python scripts/validar_marcacao.py
python scripts/parse_para_json.py
python scripts/build_pipeline.py --modo completo
```

### Modo Docker
```bash
docker build -t pipeline-editorial .
docker run --rm -v $(pwd):/app pipeline-editorial python scripts/build_pipeline.py
```

---

## 🧰 Bibliotecas Utilizadas

| Biblioteca           | Função Principal                                 |
|----------------------|--------------------------------------------------|
| `pypandoc`           | Conversão `.odt` → `.md`                         |
| `jinja2`             | Templates `.html` e `.fodt`                      |
| `ollama`             | LLM local para marcação semântica                |
| `qrcode`             | Inserção de QR codes                             |
| `hashlib`            | Cache baseado em fingerprint de entrada          |
| `logging`            | Logs por etapa, com falhas e tempos              |
| `concurrent.futures` | Execução paralela                                |
| `ebook-convert`      | Geração `.epub` com TOC                          |
| `LibreOffice`        | Geração `.odt` e `.pdf` com estilo aplicado      |

---

## 💡 Futuras Extensões (opcionais)

- Contador de palavras por capítulo para validar integridade
- Validador visual de marcações
- Exportação multilíngue com estilos compartilhados
- Interface web para revisão e diff visual
- Publicação por organização biônica ou editora digital

---

> Esta pipeline fornece uma base robusta e extensível para produção editorial profissional com IA, automação semântica e controle fino de estilo e conteúdo.

