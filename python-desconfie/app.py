"""API de extração Desconfie: recebe arquivos e consulta o ML externo."""

import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from http import HTTPStatus

import requests
from flask import Flask, has_request_context, jsonify, request
from werkzeug.exceptions import MethodNotAllowed, NotFound, RequestEntityTooLarge

from ocr import extrair_texto_imagem, validar_imagem
from pdf_reader import extrair_texto_pdf, validar_pdf
from tratamento import tratar_texto
from formatador import formatar_resultado


LIMITE_UPLOAD_BYTES = 10 * 1024 * 1024
LIMITE_TEXTO_ML = 5000
LIMITE_URLS = 5
ML_URL = os.getenv("ML_URL", "").rstrip("/")
TIMEOUT_ML = int(os.getenv("TIMEOUT_ML", "65"))

EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "pdf"}
TIPOS_POR_EXTENSAO = {
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "pdf": "application/pdf",
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = LIMITE_UPLOAD_BYTES


def corpo_erro(mensagem, codigo, *, erro=None, campos=None):
    return {
        "status": codigo,
        "erro": erro or HTTPStatus(codigo).phrase,
        "mensagem": mensagem,
        "caminho": request.path if has_request_context() else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "campos": campos or {},
    }


def resposta_erro(mensagem, codigo, *, erro=None, campos=None):
    return jsonify(corpo_erro(mensagem, codigo, erro=erro, campos=campos)), codigo


def obter_extensao(nome_arquivo):
    if "." not in nome_arquivo:
        return ""
    return nome_arquivo.rsplit(".", 1)[1].lower()


def identificar_tipo_por_assinatura(conteudo):
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if conteudo.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if conteudo.startswith(b"%PDF-"):
        return "application/pdf"
    return None


def validar_upload(nome_arquivo, conteudo):
    extensao = obter_extensao(nome_arquivo)
    if extensao not in EXTENSOES_PERMITIDAS:
        raise TypeError("Formato de arquivo nao suportado.")

    tipo_esperado = TIPOS_POR_EXTENSAO[extensao]
    tipo_identificado = identificar_tipo_por_assinatura(conteudo)
    if tipo_identificado is None:
        raise TypeError("O conteudo do arquivo nao possui formato suportado.")
    if tipo_identificado != tipo_esperado:
        raise TypeError("A extensao nao corresponde ao conteudo do arquivo.")
    return tipo_identificado


def consultar_ml(caminho, payload):
    """Retorna o JSON e o status HTTP do serviço de ML."""
    if not ML_URL:
        return corpo_erro("ML_URL nao foi configurada.", 503, erro="ML_NAO_CONFIGURADO"), 503

    try:
        resposta = requests.post(f"{ML_URL}{caminho}", json=payload, timeout=TIMEOUT_ML)
        try:
            dados = resposta.json()
        except ValueError:
            return corpo_erro("O servico ML devolveu JSON invalido.", 502, erro="RESPOSTA_ML_INVALIDA"), 502

        if not isinstance(dados, dict):
            return corpo_erro("O servico ML devolveu dados inesperados.", 502, erro="RESPOSTA_ML_INVALIDA"), 502
        if not resposta.ok:
            app.logger.warning("ML retornou status %s em %s", resposta.status_code, caminho)
            return dados, resposta.status_code
        return dados, resposta.status_code
    except requests.Timeout:
        return corpo_erro("Tempo limite da API de ML excedido.", 504, erro="TIMEOUT_ML"), 504
    except requests.RequestException:
        app.logger.exception("Falha de conexao com o servico ML")
        return corpo_erro("Nao foi possivel acessar a API de ML.", 502, erro="ML_INDISPONIVEL"), 502


def urls_do_texto(texto):
    """Identifica URLs únicas no texto completo."""
    urls = []
    vistas = set()
    padrao = (
        r"(https?://\S+|www\.\S+|"
        r"\b[\w-]+\.(?:com|net|org|xyz|top|online|"
        r"site|info|click|ly|gd|br)(?:/\S*)?)"
    )

    for achado in re.findall(padrao, texto, flags=re.IGNORECASE):
        url = achado.rstrip(".,;)")
        if url and url not in vistas and len(url) <= LIMITE_TEXTO_ML:
            vistas.add(url)
            urls.append(url)
        if len(urls) >= LIMITE_URLS:
            break
    return urls


@app.errorhandler(RequestEntityTooLarge)
def arquivo_muito_grande(erro):
    return resposta_erro("Arquivo excede o limite de 10 MB.", 413)


@app.errorhandler(MethodNotAllowed)
def metodo_nao_permitido(erro):
    return resposta_erro("Metodo HTTP nao permitido.", 405)


@app.errorhandler(NotFound)
def rota_nao_encontrada(erro):
    return resposta_erro("Rota nao encontrada.", 404)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "mlConfigurado": bool(ML_URL)}), 200


@app.get("/")
def indice():
    return jsonify({"servico": "desconfie-extracao", "status": "ok"}), 200


@app.post("/prever/texto")
def prever_texto():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return resposta_erro("Envie um objeto JSON.", 400)

    texto = dados.get("texto")
    if not isinstance(texto, str) or not texto.strip():
        return resposta_erro("O campo texto e obrigatorio.", 400)

    texto = texto.strip()
    if len(texto) > LIMITE_TEXTO_ML:
        return resposta_erro(
            f"Texto acima de {LIMITE_TEXTO_ML} caracteres.",
            400,
            erro="TEXTO_MUITO_LONGO",
            campos={"texto": f"maximo de {LIMITE_TEXTO_ML} caracteres"},
        )

    resultado, codigo = consultar_ml("/prever/texto", {"texto": texto})
    return jsonify(resultado), codigo


@app.post("/prever/url")
def prever_url():
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        return resposta_erro("Envie um objeto JSON.", 400)

    url = dados.get("url")
    if not isinstance(url, str) or not url.strip():
        return resposta_erro("O campo url e obrigatorio.", 400)

    url = url.strip()
    if len(url) > LIMITE_TEXTO_ML:
        return resposta_erro("URL acima de 5000 caracteres.", 400)

    resultado, codigo = consultar_ml("/prever/url", {"url": url})
    return jsonify(resultado), codigo


@app.post("/extrair")
def extrair():
    """Recebe arquivo do Java, extrai texto e consulta o ML."""
    arquivo = request.files.get("arquivo")
    if arquivo is None:
        return resposta_erro("O campo arquivo e obrigatorio.", 400)
    if arquivo.filename is None or not arquivo.filename.strip():
        return resposta_erro("O nome do arquivo e obrigatorio.", 400)

    try:
        conteudo = arquivo.read()
        if not conteudo:
            return resposta_erro("O arquivo enviado esta vazio.", 400)
        if len(conteudo) > LIMITE_UPLOAD_BYTES:
            return resposta_erro("Arquivo excede o limite de 10 MB.", 413)

        tipo_arquivo = validar_upload(arquivo.filename, conteudo)
        arquivo_id = request.form.get("arquivoId")
        if arquivo_id not in (None, ""):
            if not arquivo_id.isdigit():
                return resposta_erro("arquivoId deve ser numerico.", 400)
            arquivo_id = int(arquivo_id)
        else:
            arquivo_id = None

        if tipo_arquivo in ("image/png", "image/jpeg"):
            if not validar_imagem(conteudo):
                return resposta_erro("Imagem invalida ou corrompida.", 422)
            texto, metodo = extrair_texto_imagem(conteudo), "OCR"
        elif tipo_arquivo == "application/pdf":
            if not validar_pdf(conteudo):
                return resposta_erro("PDF invalido ou corrompido.", 422)
            texto, metodo = extrair_texto_pdf(conteudo), "PDF_TEXTO"
        else:
            return resposta_erro("Formato nao suportado.", 415)

        texto_completo = tratar_texto(texto)
        if not texto_completo:
            return resposta_erro("Nenhum texto reconhecido no arquivo.", 422)

        texto_ml = texto_completo[:LIMITE_TEXTO_ML]
        resultado = formatar_resultado(arquivo_id, arquivo.filename, tipo_arquivo, texto_completo, metodo)
        resultado["textoTruncadoParaML"] = len(texto_completo) > LIMITE_TEXTO_ML

        analise_texto, status = consultar_ml("/prever/texto", {"texto": texto_ml})

        # A extração é útil mesmo quando o ML está indisponível. A classificação
        # é, portanto, registrada como parcial em vez de invalidar a resposta.
        resultado["analiseML"] = {
            "texto": {"status": status, "resultado": analise_texto},
            "urls": [],
        }

        if status == 200:
            urls = urls_do_texto(texto_completo)
            # Chamadas independentes: uma URL lenta ou inválida não bloqueia as demais.
            with ThreadPoolExecutor(max_workers=LIMITE_URLS) as executor:
                futuros = {
                    executor.submit(consultar_ml, "/prever/url", {"url": url}): (indice, url)
                    for indice, url in enumerate(urls)
                }
                analises_urls = [None] * len(futuros)

                for futuro in as_completed(futuros):
                    indice, url = futuros[futuro]
                    try:
                        analise_url, status_url = futuro.result()
                    except Exception:
                        app.logger.exception("Falha inesperada ao consultar URL no ML")
                        analise_url = corpo_erro(
                            "Falha inesperada ao consultar URL no ML.",
                            502,
                            erro="ML_INDISPONIVEL",
                        )
                        status_url = 502

                    analises_urls[indice] = {
                        "url": url,
                        "status": status_url,
                        "resultado": analise_url,
                    }

            resultado["analiseML"]["urls"] = analises_urls

        return jsonify(resultado), 200
    except TypeError as erro:
        return resposta_erro(str(erro), 415)
    except ValueError as erro:
        return resposta_erro(str(erro), 422)
    except RuntimeError:
        app.logger.exception("Falha no Tesseract")
        return resposta_erro("Falha no servico OCR.", 503)
    except Exception:
        app.logger.exception("Falha inesperada ao processar o arquivo")
        return resposta_erro("Falha interna inesperada.", 500)
    finally:
        arquivo.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
