import io
import unittest
from unittest.mock import patch

import app


class TestApp(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_health_e_erros_seguem_o_contrato(self):
        self.assertEqual(self.client.get("/health").status_code, 200)
        resposta = self.client.post("/prever/texto", json={})
        corpo = resposta.get_json()
        self.assertEqual(resposta.status_code, 400)
        self.assertTrue({"status", "erro", "mensagem", "caminho", "timestamp", "campos"} <= corpo.keys())

    def test_prever_texto_rejeita_texto_acima_do_limite(self):
        resposta = self.client.post("/prever/texto", json={"texto": "a" * 5001})
        self.assertEqual(resposta.status_code, 400)
        self.assertEqual(resposta.get_json()["erro"], "TEXTO_MUITO_LONGO")

    def test_extracao_permanece_disponivel_sem_ml(self):
        with patch.object(app, "validar_imagem", return_value=True), patch.object(
            app, "extrair_texto_imagem", return_value="texto extraido"
        ), patch.object(app, "consultar_ml", return_value=({"erro": "fora do ar"}, 503)):
            resposta = self.client.post(
                "/extrair",
                data={"arquivo": (io.BytesIO(b"\x89PNG\r\n\x1a\n"), "aviso.png")},
            )

        corpo = resposta.get_json()
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(corpo["textoExtraido"], "texto extraido")
        self.assertEqual(corpo["analiseML"]["texto"]["status"], 503)

    def test_urls_sao_parciais_e_nao_interrompem_extracao(self):
        resultados = iter([
            ({"classe": "seguro"}, 200),
            ({"erro": "indisponivel"}, 503),
            ({"classe": "suspeito"}, 200),
        ])
        with patch.object(app, "validar_imagem", return_value=True), patch.object(
            app, "extrair_texto_imagem", return_value="a.com b.com"
        ), patch.object(app, "consultar_ml", side_effect=lambda *args: next(resultados)):
            resposta = self.client.post(
                "/extrair",
                data={"arquivo": (io.BytesIO(b"\x89PNG\r\n\x1a\n"), "aviso.png")},
            )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.get_json()["analiseML"]["urls"]), 2)


if __name__ == "__main__":
    unittest.main()
