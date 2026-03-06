from pathlib import Path
import fitz
import re
import os
import edge_tts
import json

VOZ = "pt-BR-AntonioNeural"
RATE = "-5%"
PASTA_SAIDA = "audios"
os.makedirs(PASTA_SAIDA, exist_ok=True)

DICIONARIO_FONETICO = {
    "acpi": "a cê pê i", "maxcpus": "max cê pê ús", "lsusb": "ele esse u esse bê",
    "lspci": "ele esse pê cê i", "lsmod": "ele esse móde", "modprobe": "móde proube",
    "modinfo": "módi info", "dmesg": "dê messege", "journalctl": "jornalê controul",
    "/sys/": "barra sís barra", "/proc/": "barra próqui barra", "/dev/": "barra dév barra",
    "/etc/": "barra éte cê barra", "root": "rút", "udev": "u dév", "dbus": "dí bus",
    "etc.": "eticétera", "etc": "eticétera", "systemd": "sístem dê",
}

HEADER_FOOTER_PATTERNS = [
    r"LPIC-1\s*\(\d{3}\)\s*\(Version\s*[\d\.]+\)", r"learning\.lpi\.org",
    r"Licenciado sob CC BY-NC-ND", r"Version:\s*[\d\.]+", r"^\s*\d+\s*$", r"^\d+\s*\|\s*learning",
]

def _apply_phonetics(text):
    for termo in ["/sys/", "/proc/", "/dev/", "/etc/"]:
        if termo in DICIONARIO_FONETICO:
            text = text.replace(termo, f" {DICIONARIO_FONETICO[termo]} ")
    for termo in sorted(DICIONARIO_FONETICO.keys(), key=len, reverse=True):
        if "/" in termo: continue
        pron = DICIONARIO_FONETICO[termo]
        text = re.sub(r'\b' + re.escape(termo) + r'\b', f" {pron} ", text, flags=re.IGNORECASE)
    def soletra_desconhecido(m):
        word = m.group(0)
        if not re.search(r'[aeiouAEIOU]', word) and len(word) >= 2: return " ".join(list(word))
        return word
    return re.sub(r'\b[a-zA-Z]{2,4}\b', soletra_desconhecido, text)

def limpar_texto(texto):
    texto = texto.replace("•", "").replace("·", "").replace("⁄", "/").replace("∕", "/")
    linhas = texto.splitlines()
    out = []
    for linha in linhas:
        linha = linha.strip()
        if not linha or any(re.search(p, linha, re.I) for p in HEADER_FOOTER_PATTERNS): continue
        if out and not re.search(r"[.!?;:]$", out[-1]): out[-1] = out[-1] + " " + linha
        else: out.append(linha)
    texto = _apply_phonetics("\n".join(out))
    return re.sub(r"\s+", " ", texto).strip()

def _nome_deterministico(titulo):
    m = re.search(r"\b(10[1-4])\.(\d)\b", titulo)
    return f"{m.group(1)}_{m.group(2)}.mp3" if m else "extra.mp3"

def gerar_manifest(caminho_arquivo):
    # Mantém compatibilidade com PDF e adiciona suporte básico para DOCX (manifest já pode ser gerado no preview DOCX).
    if str(caminho_arquivo).lower().endswith(".docx"):
        # Recria um manifest simples a partir dos MP3 existentes na pasta 'audios'
        manifest = {}
        # Ordenação: 101, 101_1, 101_2..., 102, 102_1...
        def _ordem(nome):
            m = re.match(r"^(10[1-4])(?:_(\d+))?\.mp3$", nome)
            if not m:
                return (999, 999)
            cap = int(m.group(1))
            sub = int(m.group(2)) if m.group(2) else 0
            return (cap, sub)
        arquivos = sorted([f for f in os.listdir(PASTA_SAIDA) if f.lower().endswith(".mp3")], key=_ordem)
        for i, fname in enumerate(arquivos):
            key = f"item_{i:03d}"
            titulo = fname.replace(".mp3","").replace("_",".")
            manifest[key] = {"titulo": titulo, "mp3": f"audios/{fname}", "inicio": "-", "fim": "-"}
        with open("manifest.json", "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=4, ensure_ascii=False)
        return

    motor = MotorAudio(caminho_arquivo)
    itens = motor.obter_sumario()
    manifest = {}
    for i, item in enumerate(itens):
        prox = itens[i+1][2] if i+1 < len(itens) else motor.doc.page_count + 1

        manifest[f"topico_{i}"] = {
            "titulo": item[1], "mp3": f"audios/{_nome_deterministico(item[1])}",
            "inicio": item[2], "fim": prox - 1
        }
    with open("manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4, ensure_ascii=False)

class MotorAudio:

    def __init__(self, caminho_pdf):
        self.caminho_pdf = caminho_pdf
        self.doc = None
    def abrir_doc(self):
        if not self.doc: self.doc = fitz.open(self.caminho_pdf)
    def obter_sumario(self):
        self.abrir_doc()
        toc = self.doc.get_toc()
        filtrado, vistos = [], set()
        for item in toc:
            m = re.search(r"\b(10[1-4])\.(\d)\b", item[1])
            if m and f"{m.group(1)}_{m.group(2)}" not in vistos:
                vistos.add(f"{m.group(1)}_{m.group(2)}"); filtrado.append(item)
        return filtrado
    async def extrair_e_converter(self, item_sumario, proxima_pag_0based, forcar=False):
        caminho = os.path.join(PASTA_SAIDA, _nome_deterministico(item_sumario[1]))
        if not forcar and os.path.exists(caminho): return True
        self.abrir_doc()
        pag_inicio = max(0, item_sumario[2] - 1) if ".1 " in item_sumario[1] else item_sumario[2] - 1
        texto = []
        for p in range(pag_inicio, proxima_pag_0based):
            page = self.doc[p]
            texto.append(page.get_text("text", clip=fitz.Rect(0, 0, page.rect.width, page.rect.height - 45)))
        await edge_tts.Communicate(limpar_texto("\n".join(texto)), VOZ, rate=RATE).save(caminho)
        return True


# ---------------------------
# MODO DOCX (teste controlado)
# ---------------------------

_DOCX_NOISE_PATTERNS = [
    r"LPIC-1\s*\(\d{3}\)\s*\(Version\s*[\d\.]+\)",
    r"learning\.lpi\.org",
    r"Licenciado\s+sob\s+CC\s+BY-NC-ND",
    r"Version:\s*\d{4}-\d{2}-\d{2}",
    r"Version:\s*[\d\.]+",
    r"^\s*\d+\s*$",
]

def _extract_after_marker(line: str, marker_regex: str) -> str | None:
    m = re.search(marker_regex, line, flags=re.I)
    if not m:
        return None
    # pega do início do marcador até o fim da linha
    start = m.start()
    out = line[start:].strip()
    if "|" in out:
        # se for tipo ".... | Tópico 101: ...."
        out = out.split("|")[-1].strip()
    return out

def _extract_titles_from_text(raw_text: str, cap: str, sub: str) -> tuple[str, str]:
    master = None
    sub_title = None
    for ln in raw_text.splitlines():
        ln = ln.strip()
        if not master:
            master = _extract_after_marker(ln, rf"\bT[óo]pico\s+{re.escape(cap)}\b")
        if not sub_title:
            sub_title = _extract_after_marker(ln, rf"\b{re.escape(cap)}\.{re.escape(sub)}\b")
        if master and sub_title:
            break
    if not master:
        master = f"Tópico {cap}"
    if not sub_title:
        sub_title = f"{cap}.{sub}"
    return master, sub_title

def _iter_docx_blocks(doc):
    # Itera parágrafos e tabelas na ordem do body
    from docx.oxml.table import CT_Tbl
    from docx.oxml.text.paragraph import CT_P
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    for child in doc.element.body.iterchildren():
        if isinstance(child, CT_P):
            yield Paragraph(child, doc)
        elif isinstance(child, CT_Tbl):
            yield Table(child, doc)

def _read_docx_text(docx_path: str) -> str:
    from docx import Document
    d = Document(docx_path)
    chunks = []
    for block in _iter_docx_blocks(d):
        if hasattr(block, "text"):  # Paragraph
            t = (block.text or "").strip()
            if t:
                chunks.append(t)
        else:
            # Table: preferência do projeto é ignorar 100% tabelas
            continue
    return "\n".join(chunks)

def limpar_texto_docx(texto: str) -> str:
    texto = texto.replace("•", "").replace("·", "").replace("⁄", "/").replace("∕", "/")
    linhas = [ln.strip() for ln in texto.splitlines() if ln.strip()]
    out = []
    for ln in linhas:
        if any(re.search(p, ln, flags=re.I) for p in _DOCX_NOISE_PATTERNS):
            continue
        # remove linhas muito curtas típicas de numeração isolada
        if re.fullmatch(r"\d{1,3}", ln):
            continue
        out.append(ln)
    # remove repetições muito frequentes (assinatura por repetição simples dentro do arquivo)
    freq = {}
    for ln in out:
        key = re.sub(r"\s+", " ", ln.lower()).strip()
        if len(key) <= 8:
            continue
        freq[key] = freq.get(key, 0) + 1
    cleaned = []
    for ln in out:
        key = re.sub(r"\s+", " ", ln.lower()).strip()
        if freq.get(key, 0) >= 3 and len(key) < 120:
            # provável cabeçalho/rodapé repetido
            continue
        cleaned.append(ln)
    texto2 = _apply_phonetics(" ".join(cleaned))
    return re.sub(r"\s+", " ", texto2).strip()

async def gerar_preview_docx(pasta_docx, preview_alvo="101_1", forcar=False):
    # Gera somente o alvo solicitado no preview (101_1 por padrão; 102_1 sob demanda).
    pasta_docx = str(pasta_docx)
    if preview_alvo not in {"101_1", "102_1"}:
        raise ValueError(f"Preview DOCX inválido: {preview_alvo}")
    alvo = os.path.join(pasta_docx, f"meu_livro_{preview_alvo}.docx")
    arquivos = [alvo]
    for a in arquivos:
        if not os.path.exists(a):
            raise FileNotFoundError(f"Arquivo DOCX não encontrado: {a}")

    manifest = {}
    idx = 0

    for docx_path in arquivos:
        fname = os.path.basename(docx_path)
        m = re.search(r"meu_livro_(10[1-4])_(\d+)\.docx$", fname, flags=re.I)
        if not m:
            raise ValueError(f"Nome inválido para preview DOCX: {fname}")
        cap = m.group(1)
        sub = m.group(2)

        raw = _read_docx_text(docx_path)
        master_title, sub_title = _extract_titles_from_text(raw, cap, sub)

        # 1) tópico mestre (curto)
        master_mp3 = os.path.join(PASTA_SAIDA, f"{cap}.mp3")
        if forcar or not os.path.exists(master_mp3):
            await edge_tts.Communicate(master_title, VOZ, rate=RATE).save(master_mp3)

        manifest[f"item_{idx:03d}"] = {
            "titulo": master_title,
            "mp3": f"audios/{cap}.mp3",
            "inicio": "DOCX",
            "fim": "DOCX",
        }
        idx += 1

        # 2) subtópico
        sub_mp3 = os.path.join(PASTA_SAIDA, f"{cap}_{sub}.mp3")
        if forcar or not os.path.exists(sub_mp3):
            body = limpar_texto_docx(raw)
            # garante que o áudio começa pelos títulos desejados
            texto_final = f"{master_title}. {sub_title}. {body}".strip()
            await edge_tts.Communicate(texto_final, VOZ, rate=RATE).save(sub_mp3)

        manifest[f"item_{idx:03d}"] = {
            "titulo": sub_title,
            "mp3": f"audios/{cap}_{sub}.mp3",
            "inicio": "DOCX",
            "fim": "DOCX",
        }
        idx += 1

    with open("manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=4, ensure_ascii=False)

    return manifest
