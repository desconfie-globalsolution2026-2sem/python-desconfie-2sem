
import io
import pdfplumber
from pdfminer.pdfparser import PDFSyntaxError


def validar_pdf(bytes_pdf):
    # 1. Verifica se o conteúdo possui a assinatura de PDF
    if not bytes_pdf.startswith(b"%PDF-"):
        return False

    # 2. Tenta abrir o PDF em memória
    try:
        fluxo = io.BytesIO(bytes_pdf)

        with pdfplumber.open(fluxo) as pdf:
            # 3. Verifica se existe pelo menos uma página
            if not pdf.pages:
                return False

        return True

    except (PDFSyntaxError, OSError, ValueError, TypeError):
        return False


def extrair_texto_pdf(bytes_pdf):
    fluxo = io.BytesIO(bytes_pdf)

    with pdfplumber.open(fluxo) as pdf:
        textos = []

        for pagina in pdf.pages:
            texto = pagina.extract_text()

            if texto:
                textos.append(texto)

    return "\n".join(textos)

