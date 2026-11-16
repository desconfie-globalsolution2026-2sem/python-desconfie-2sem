import io
import pdfplumber 
import os


def validar_pdf(bytes_pdf):
     # 1. Verifica se o arquivo existe no caminho informado
    if not os.path.isfile(caminho_arquivo):
        return False

    # 2. Verifica os primeiros 5 bytes (assinatura padrão de PDF)
    try:
        with open(caminho_arquivo, "rb") as f:
            cabecalho = f.read(5)
            if cabecalho != b"%PDF-":
                return False
    except Exception:
        return False

    # 3. Tenta abrir com o pdfplumber para garantir que não está corrompido
    try:
        with pdfplumber.open(caminho_arquivo) as pdf:
            # Verifica se há pelo menos uma página legível
            if len(pdf.pages) == 0:
                return False
        return True
    except (PDFSyntaxError, Exception):
        return False
    pass


def extrair_texto_pdf(bytes_pdf):
    fluxo = io.BytesIO(bytes_pdf)

    with pdfplumber.open(fluxo) as pdf:
        textos = []

        for pagina in pdf.pages:
            texto = pagina.extract_text()

            if texto:
                textos.append(texto)

    return "\n".join(textos)
