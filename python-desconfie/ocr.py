
import io
from PIL import Image, UnidentifiedImageError
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

# Valida se a imagem segue as regras de formato exigidos pelo sistema 

def validar_imagem(caminho):
    try:
        with Image.open(caminho) as img:

            if img.format not in ("PNG", "JPEG"):
                print("Formato não permitido.")
                return False

            img.verify()

        return True

    except (UnidentifiedImageError, OSError, SyntaxError) as erro:
        print(f"Erro ao validar imagem: {erro}")
        return False

if __name__ == "__main__":
    resultado = validar_imagem("teste.png")
    print("Resultado da validação:", resultado)



