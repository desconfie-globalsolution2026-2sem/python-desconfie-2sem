
import io
from PIL import Image
import pytesseract

# Abre a imagem recebida e extrai o texto com Tesseract
def extrair_texto_imagem(fluxo_imagem):

    fluxo = io.BytesIO(fluxo_imagem)

    with Image.open(fluxo) as imagem:
        imagem = imagem.convert('L')

        texto = pytesseract.image_to_string(
            imagem,
            lang='por'
        )

    return texto


