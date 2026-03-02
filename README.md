# Audiobook-App

Aplicativo (Python + Flet) para gerar **audiobooks em MP3** e um **`manifest.json`** a partir de conteúdos de estudo (PDF e/ou DOCX).

**Escopo intencional:** o app é um **gerador** (não um player). A reprodução/estudo é feita no **Player do Windows**.

---

## O que o app gera

- Arquivos **.mp3** organizados por tópico/subtópico
- Um arquivo **`manifest.json`** com a estrutura e metadados dos áudios (para consumo pelo app e/ou outros módulos como quiz)

---

## Entradas suportadas

- **PDF** (principal)
- **DOCX** (fallback / alternativa, especialmente útil quando o PDF causa leitura errada de rodapés/cabeçalhos)

> Observação importante do material: o subtópico **104_4 não existe** no conteúdo original (pulo de 104.3 para 104.5). Portanto, é normal não haver arquivo `meu_livro_104_4.*`.

---

## Estrutura recomendada do projeto

Arquivos principais (código):
- `main.py` — ponto de entrada do app
- `interface.py` — interface (Flet)
- `motor_audio.py` — motor de leitura/limpeza/TTS e geração de MP3/manifest

Saídas oficiais:
- `audiobook_app/audios/` — MP3 gerados
- `audiobook_app/manifest.json` — manifest oficial gerado

Documentação:
- `docs/LOG_PROGRESSO.txt` — histórico e decisões do projeto (opcional, mas recomendado)

---

## Como executar (fluxo real)

O projeto é executado pelo **VS Code** via terminal com:

```bash
flet run main.py
