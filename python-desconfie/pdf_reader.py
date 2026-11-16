
import io
import pdfplumber


def validar_pdf(bytes_pdf):
    try:
        fluxo = io.BytesIO(bytes_pdf)

        with pdfplumber.open(fluxo) as pdf:
            # Verificar se o PDF possui páginas
            pass

        return True

    except Exception:
        return False


