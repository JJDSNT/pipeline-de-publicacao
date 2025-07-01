# 🚀 Pipeline de Publicação Editorial

> Uma pipeline automatizada, modular e extensível para transformar arquivos `.odt` em publicações profissionais nos formatos `.pdf` e `.epub`, com marcação semântica por LLM, estilos configuráveis, cache por hash, paralelismo, validações e suporte completo a workflows com Git e Docker.

---

## ⚙️ Arquitetura Geral

Esta pipeline está organizada em **duas grandes etapas**:

1. **Marcação Semântica com LLM** — conversão `.odt` → `.md`, marcação com IA, validação e parsing para JSON.
2. **Formatação e Publicação** — aplicação de estilos com templates `jinja2` e geração de `.fodt`, `.html`, `.pdf`, `.epub`.

A arquitetura permite:

- Controle total sobre conteúdo, estilo e ordem dos capítulos
- Geração de páginas especiais como capa, créditos, epígrafes e colofão
- Sumário automático nos formatos `.odt/.pdf` (via LibreOffice) e `.epub` (via Calibre)
- Estilos centralizados em JSON para ODT e CSS
- Paralelismo e cache para desempenho e robustez
- Execução local ou via Docker

---

## 🧩 Etapa 1 — Marcação Semântica com LLM

### 🎯 Objetivo

Transformar documentos `.odt` em arquivos `.md` com **marcações semânticas explícitas** (`[TITULO1]`, `[CORPO_DO_TEXTO]`, etc.), usando modelos LLM locais via Ollama, com validação e parsing para JSON.

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

- ✅ Conversão `.odt` → `.md` com `pandoc` via `pypandoc`
- ✅ Marcação semântica com LLM via `ollama`
- ✅ Fallback automático (modelo alternativo, divisão por chunk)
- ✅ Validação: balanceamento de tags + fidelidade ao texto original
- ✅ Cache baseado em `hash(md5)` do conteúdo
- ✅ Paralelismo com `concurrent.futures.ProcessPoolExecutor`
- ✅ Logs estruturados com `logging` nativo do Python
- ✅ Versionamento via Git dos arquivos `.md` marcados

---

## 🎨 Etapa 2 — Formatação e Publicação

### 🎯 Objetivo

Renderizar os conteúdos `.json` estruturados com `jinja2`, aplicar estilos visuais e gerar `.fodt`, `.html`, `.odt`, `.pdf` e `.epub`.

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
│   └── style.css
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

### 🧠 Funcionalidades

- ✅ Templates `jinja2` com cache pré-compilado
- ✅ Estilos definidos em `estilos_definicoes.json` (ODT e CSS)
- ✅ Páginas geradas automaticamente (capa, créditos, epígrafe etc.)
- ✅ Inserção de QR codes com `qrcode`
- ✅ EPUB via `ebook-convert` (Calibre)
- ✅ PDF e ODT via `LibreOffice` (`soffice`)
- ✅ TOC automático para `.odt/.pdf` e `.epub`

---

## 📜 Exemplo de Manifesto

```json
{
  "modelo_llm": "phi3:mini",
  "ordem": [
    "capa_falsa",
    "ficha_catalografica",
    "epigrafe",
    "capitulo1",
    "capitulo2",
    "colofao"
  ],
  "estilos": "estilos_definicoes.json",
  "formato": "A5",
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
      "cor": "#2C5282",
      "espacamento_antes": "24pt",
      "espacamento_depois": "12pt"
    },
    "css": {
      "classe": "titulo-principal",
      "propriedades": {
        "font-family": "Arial Black, sans-serif",
        "font-size": "1.8em",
        "color": "#2C5282",
        "margin-top": "1.5em",
        "margin-bottom": "0.75em"
      }
    }
  },
  "CORPO_DO_TEXTO": {
    "odt": {
      "nome_estilo": "Texto Corpo",
      "fonte": "Liberation Serif",
      "tamanho": "12pt",
      "cor": "#000000",
      "espacamento_antes": "0pt",
      "espacamento_depois": "6pt",
      "recuo_primeira_linha": "1.2cm"
    },
    "css": {
      "classe": "corpo-texto",
      "propriedades": {
        "font-family": "Georgia, serif",
        "font-size": "1em",
        "color": "#000000",
        "text-indent": "2em",
        "margin-bottom": "1em",
        "line-height": "1.6"
      }
    }
  }
}
```

---

## 🧰 Bibliotecas Utilizadas

| Biblioteca      | Função Principal                             |
|-----------------|-----------------------------------------------|
| `pypandoc`      | Conversão `.odt` → `.md`                      |
| `jinja2`        | Templates HTML e FODT                         |
| `ollama`        | Modelos LLM locais                            |
| `qrcode`        | Inserção de QR Codes                          |
| `hashlib`       | Cache baseado em fingerprint de conteúdo      |
| `logging`       | Logs por etapa                                |
| `concurrent.futures` | Execução paralela                        |
| `ebook-convert` | Geração de `.epub`                            |
| `LibreOffice`   | Geração de `.odt` e `.pdf` com `--headless`   |

---

## 🧪 Execução

### Local
```bash
python scripts/converter_odt_para_md.py
python scripts/marcar_com_llm.py
python scripts/validar_marcacao.py
python scripts/parse_para_json.py
python scripts/build_pipeline.py
```

### Docker
```bash
docker build -t pipeline-editorial .
docker run --rm -v $(pwd):/app pipeline-editorial python scripts/build_pipeline.py
```

---

## 💡 Possibilidades Futuras

- Validador visual de marcação semântica
- Interface web de revisão e preview
- Exportação multilíngue
- Diff visual entre versões
- Publicação por organização biônica

---

> Esta pipeline entrega uma base editorial sólida, confiável e extensível — com IA, automação e controle fino sobre conteúdo, estilo e publicação.
