"""Testes de integração e tratamento de erros do módulo OCR."""
import io
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw
import pytesseract


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import ocr  # noqa: E402


class TestOCR(unittest.TestCase):
    @staticmethod
    def criar_imagem(formato):
        """Cria uma imagem simples em memória, sem depender de arquivos locais."""
        imagem = Image.new("RGB", (480, 120), "white")
        ImageDraw.Draw(imagem).text((20, 45), "TESTE OCR 123", fill="black")
        conteudo = io.BytesIO()
        imagem.save(conteudo, format=formato)
        return conteudo.getvalue()

    def test_tesseract_tem_idioma_portugues(self):
        """Confirma que o executável e os dados de idioma necessários existem."""
        self.assertTrue(str(pytesseract.get_tesseract_version()))
        self.assertIn("por", pytesseract.get_languages(config=""))

    def test_png_eh_valido_e_texto_eh_extraido(self):
        dados = self.criar_imagem("PNG")

        self.assertTrue(ocr.validar_imagem(dados))
        self.assertIn("TESTE", ocr.extrair_texto_imagem(dados).upper())

    def test_jpeg_eh_valido_e_texto_eh_extraido(self):
        dados = self.criar_imagem("JPEG")

        self.assertTrue(ocr.validar_imagem(dados))
        self.assertIn("TESTE", ocr.extrair_texto_imagem(dados).upper())

    def test_arquivo_invalido_retorna_false(self):
        self.assertFalse(ocr.validar_imagem(b"isto nao e uma imagem"))

    def test_erro_do_tesseract_vira_runtime_error(self):
        dados = self.criar_imagem("PNG")

        with patch.object(
            ocr.pytesseract,
            "image_to_string",
            side_effect=ocr.pytesseract.TesseractError(1, "falha simulada"),
        ):
            with self.assertRaisesRegex(RuntimeError, "Falha ao executar o Tesseract OCR"):
                ocr.extrair_texto_imagem(dados)


if __name__ == "__main__":
    unittest.main()
