# 🚀 Pipeline de Publicação Editorial

> Uma pipeline automatizada, modular e extensível para transformar arquivos `.odt` em publicações profissionais no formato `.epub` (e futuramente `.pdf`), usando conversões determinísticas, marcação limpa em Markdown e empacotamento controlado em HTML.

---

## ⚙️ Arquitetura Geral

A pipeline está organizada em três etapas principais:

1. **Conversão de `.odt` para `.md`** — geração de arquivos Markdown por capítulo.  
2. **Transformação de `.md` para `.html`** — um arquivo HTML por capítulo ou seção.  
3. **Montagem do EPUB final** — com capa, sumário, partes, capítulos e extras, conforme estrutura de livro técnico.

---

## 🧩 Etapa 1 — Conversão `.odt` → `.md`

### 🎯 Objetivo

Extrair conteúdo limpo e estruturado de arquivos `.odt`, mantendo títulos, listas e ênfases, para edição e organização futura.

### 🛠️ Ferramenta

- `pandoc` via CLI ou `pypandoc`

### 📁 Estrutura

input/pt_br/capitulos/*.odt  
↓  
gerado_automaticamente/pt_br/markdown/*.md

---

## 🧩 Etapa 2 — Conversão `.md` → `.html`

### 🎯 Objetivo

Transformar cada capítulo `.md` em um arquivo `.html` isolado, mantendo estrutura mínima para EPUB (headings, parágrafos, listas).

### 🛠️ Ferramentas

- `Python-Markdown`  
- ou `pandoc`

### 📁 Estrutura

gerado_automaticamente/pt_br/markdown/cap01.md  
↓  
gerado_automaticamente/pt_br/html/parte_01_capitulo_01.html

---

## 🧩 Etapa 3 — Geração do EPUB

### 🎯 Objetivo

Montar um EPUB completo, estruturado por partes e capítulos, com elementos pré-textuais e pós-textuais, CSS, capa e sumário navegável.

### 🛠️ Ferramentas possíveis

- `ebooklib` — controle programático completo (AGPL)  
- `pypub` — API simples  
- `pandoc` — para geração rápida (menos controle)

### 📁 Estrutura HTML esperada

capa.html  
falsa_capa.html  
pagina_de_rosto.html  
pagina_de_creditos.html  
dedicatoria.html  
agradecimentos.html  
epigrafe.html  
sumario.html  
introducao_geral.html  
parte_01_introducao.html  
parte_01_capitulo_01.html  
parte_01_capitulo_02.html  
...  
parte_05_capitulo_xx.html  
conclusao_geral.html  
apendices.html  
anexos.html  
glossario.html  
referencias.html  
sobre_o_autor.html

---

## 📦 Organização do Projeto

projetos/  
└── liderando_transformacao/  
  ├── input/  
  │  └── pt_br/  
  │   └── capitulos/  
  ├── gerado_automaticamente/  
  │  └── pt_br/  
  │   ├── markdown/  
  │   ├── html/  
  │   └── epub/  
  ├── output/  
  │  └── livro.epub  
  ├── estilos/  
  ├── scripts/  
  └── logs/

---

## 📜 Exemplo de Manifesto (futuro)

{
  "idioma": "pt_br",
  "titulo": "Liderando a Transformação Digital",
  "autor": "Jaime Dias",
  "capa": "input/pt_br/images/capa.jpg",
  "estrutura": [
    "falsa_capa",
    "pagina_de_rosto",
    "epigrafe",
    "parte_01_introducao",
    "parte_01_capitulo_01",
    "parte_01_capitulo_02",
    "...",
    "referencias",
    "sobre_o_autor"
  ]
}

---

## ✅ Funcionalidades já disponíveis

- ✅ Conversão `.odt` → `.md` com Pandoc  
- ✅ Conversão `.md` → `.html` com `markdown` ou `pandoc`  
- ✅ Separação por partes e capítulos  
- ✅ Suporte a elementos estruturais pré/pós-textuais  
- ✅ Geração de EPUB com múltiplos HTMLs

---

## 🔄 Futuro: Etapas complementares

- 📘 Geração de `.pdf` com controle de estilo (`wkhtmltopdf`, `WeasyPrint`, ou `LibreOffice`)  
- 🎨 Geração automática de sumário (`toc.xhtml`)  
- 🔍 Validação EPUB com `epubcheck`  
- 📊 Contador de palavras por capítulo  
- 🌐 Publicação multilíngue e controle por `config.json`

---

> Esta pipeline é pensada para garantir **controle total**, **simplicidade na manutenção** e **alta qualidade técnica** para publicação editorial multiplataforma, começando por EPUB e evoluindo para PDF.
