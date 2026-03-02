# Audiobook-App — Progresso / Status do Projeto

> Documento curto para acompanhar **o que já foi feito**, **o que está em andamento** e **o que falta**.  
> Ambiente-alvo: **Windows 11**.  
> Saídas oficiais: `audiobook_app/audios/` e `audiobook_app/manifest.json`.

---

## Estado atual (visão geral)

- ✅ App funciona como **gerador** de MP3 + manifest
- ✅ Estrutura de pastas oficial consolidada (evita confusão de saídas antigas)
- ✅ Ambiente e dependências principais validados
- ⚠️ Ainda há problemas de narração (rodapés/boilerplate, símbolos em comandos, tabelas)

---

## Feito ✅

### Arquitetura / UX
- Decisão de escopo: **app = gerador**, reprodução via **Player do Windows** (player embutido teve UX inconsistente).

### Ambiente validado
- Windows 11
- Python (venv) 3.12.0
- Flet 0.28.3
- flet-audio 0.1.0
- PyMuPDF 1.27.1
- edge-tts 7.2.7
- python-docx OK

### Estrutura oficial de pastas
- Raiz: `C:\Estudos\LPIC1_APP\`
- App: `C:\Estudos\LPIC1_APP\audiobook_app\`
- Saídas oficiais:
  - MP3: `audiobook_app/audios/`
  - Manifest: `audiobook_app/manifest.json`
- Arquivamento de itens antigos na raiz para não confundir:
  - `audios` → `audios__VAZIA_NAO_USAR`
  - `manifest.json` → `manifest__OLD_2026-02-16.json`

### Conteúdo de entrada (material)
- PDFs fragmentados: `meu_livro_101_1.pdf ... meu_livro_104_7.pdf`
- DOCX fragmentados (fallback/testes): `meu_livro_101_1.docx ... meu_livro_104_7.docx`
- **Nota do material:** `104_4` não existe (pulo do 104.3 para 104.5 no original). Isso é esperado.

### Saídas de teste (ainda não validadas para estudo)
- `101.mp3`, `101_1.mp3`, `102.mp3`, `102_1.mp3` (temporários/diagnóstico)

---

## Em andamento ⚙️

### Qualidade do áudio / pipeline
- Reduzir/evitar narração de:
  - rodapés/cabeçalhos e **boilerplate repetido**
  - tabelas (preferência: **ignorar 100%**)
- Normalizar símbolos em comandos (para não “sumirem” na fala)

### Estratégia de entrada
- Manter **PDF-first** e **DOCX fallback**
  - DOCX é útil quando o PDF embaralha ordem de leitura ou inclui rodapés no fluxo

---

## Problemas conhecidos ⚠️

- Rodapés/cabeçalhos podem ser narrados, especialmente quando conversões colocam “rodapé” no corpo (body).
- Tabelas com leitura inconsistente (pula, repete, confunde ordem).
- Símbolos em comandos podem ser “engolidos” (`-`, `/`, `<`, `>`, `|`, `>>`, `2>` etc.).
- Duplicação do “Tópico Mestre” observada no início do `101_1` (não bloqueante, mas ideal corrigir).

---

## Próximas ações (prioridade) 🧭

1) **Normalização de símbolos em comandos** (apenas em contexto de comando/bloco de código)  
   - Ex.: `-` → “traço”, `/` → “barra”, `<`/`>` → “menor/maior que”, `|` → “pipe”.

2) **Ignorar 100% tabelas** no processo de extração/narração.

3) **Filtro mínimo de boilerplate** (rodapé/cabeçalho):
   - padrões óbvios + repetição
   - evoluir para “assinatura por documento” se necessário

4) **Modo Preview** (teste rápido):
   - gerar apenas `101_1.mp3` (e depois `102_1.mp3`) para validar cortes/filtros sem processar lote inteiro

---

## Integração futura: Quiz 🧩

- `quiz_generator` deve consumir o manifest oficial:
  - `audiobook_app/manifest.json`
- Fluxo desejado:
  - Abrir texto (PDF/DOCX)
  - Abrir áudio (MP3 no Player do Windows)
  - Rodar quiz por tópico/subtópico

---

## Convenções de versionamento (GitHub)

Este repositório deve conter **somente código e documentação**.

Não versionar:
- `venv/`, caches
- `audiobook_app/audios/`, `*.mp3`
- `audiobook_app/manifest.json` (se for gerado)
- PDFs/DOCX do material (por tamanho/direitos autorais)

Use `.gitignore` para garantir isso.
