import io
from PIL import Image, UnidentifiedImageError
import pytesseract

# Abre a imagem recebida e extrai o texto com Tesseract
def extrair_texto_imagem(bytes_imagem):
    try:
        fluxo = io.BytesIO(bytes_imagem)

        with Image.open(fluxo) as imagem:
            imagem = imagem.convert("L")

            texto = pytesseract.image_to_string(
                imagem,
                lang="por"
            )

        return texto

    except (
        pytesseract.TesseractNotFoundError,
        pytesseract.TesseractError
    ) as erro:
        raise RuntimeError(
            "Falha ao executar o Tesseract OCR."
        ) from erro

    except (UnidentifiedImageError, OSError, ValueError) as erro:
        raise ValueError("Imagem inválida ou corrompida.") from erro

# Valida se a imagem segue as regras de formato exigidos pelo sistema 
def validar_imagem(bytes_imagem):
    try:
        fluxo = io.BytesIO(bytes_imagem)

        with Image.open(fluxo) as imagem:
            formato = imagem.format

            if formato not in ("PNG", "JPEG"):
                return False

            imagem.verify()

        # Verifica também se os pixels podem ser decodificados
        with Image.open(io.BytesIO(bytes_imagem)) as imagem:
            imagem.load()

        return True

    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        return False




if __name__ == "__main__":
    with open("teste.png", "rb") as arquivo:
        conteudo = arquivo.read()

    resultado = validar_imagem(conteudo)
    print("Imagem válida:", resultado)

    if resultado:
        try:
            texto = extrair_texto_imagem(conteudo)
            print("Texto extraído:")
            print(texto)

        except (ValueError, RuntimeError) as erro:
            print("Erro:", erro)



