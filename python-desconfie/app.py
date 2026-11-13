"""Estrutura inicial da API Flask para recebimento de arquivos."""
import os
from flask import Flask, jsonify, request
from werkzeug.exceptions import MethodNotAllowed, RequestEntityTooLarge

LIMITE_UPLOAD_BYTES = 10 * 1024 * 1024
EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "pdf"}
TIPOS_POR_EXTENSAO = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "pdf": "application/pdf"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = LIMITE_UPLOAD_BYTES


def resposta_erro(mensagem, codigo):
    """Monta uma resposta JSON segura para erros da API."""
    return jsonify({"sucesso": False, "erro": mensagem}), codigo


def obter_extensao(nome_arquivo):
    """Retorna a extensao declarada em minusculas ou uma string vazia."""
    if "." not in nome_arquivo:
        return ""
    return nome_arquivo.rsplit(".", 1)[1].lower()


def identificar_tipo_por_assinatura(conteudo):
    """Identifica PNG, JPEG ou PDF por suas assinaturas basicas de bytes."""
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if conteudo.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if conteudo.startswith(b"%PDF-"):
        return "application/pdf"
    return None


def validar_upload(nome_arquivo, conteudo):
    """Valida extensao e assinatura, retornando o tipo MIME confirmado."""
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


@app.errorhandler(RequestEntityTooLarge)
def arquivo_muito_grande(erro):
    """Retorna JSON quando o limite configurado pelo Flask e excedido."""
    return resposta_erro("Arquivo excede o limite de 10 MB.", 413)


@app.errorhandler(MethodNotAllowed)
def metodo_nao_permitido(erro):
    """Mantem respostas JSON para metodo HTTP invalido."""
    return resposta_erro("Metodo HTTP nao permitido.", 405)


@app.route("/extrair", methods=["POST"])
def extrair():
    """Recebe e valida upload multipart/form-data, sem processar o arquivo."""
    arquivo = request.files.get("arquivo")
    if arquivo is None:
        return resposta_erro("O campo arquivo e obrigatorio.", 400)
    if arquivo.filename is None or arquivo.filename.strip() == "":
        return resposta_erro("O nome do arquivo e obrigatorio.", 400)
    try:
        conteudo = arquivo.read()
        if not conteudo:
            return resposta_erro("O arquivo enviado esta vazio.", 400)
        if len(conteudo) > LIMITE_UPLOAD_BYTES:
            return resposta_erro("Arquivo excede o limite de 10 MB.", 413)
        tipo_arquivo = validar_upload(arquivo.filename, conteudo)

        # Futuramente: ocr.py/pdf_reader.py, tratamento.py e formatador.py.
        return jsonify({"sucesso": True, "mensagem": "Arquivo recebido e validado com sucesso",
                        "arquivo": {"nome": arquivo.filename, "tipo": tipo_arquivo}, "status": "RECEBIDO"}), 200
    except TypeError as erro:
        return resposta_erro(str(erro), 415)
    except Exception:
        app.logger.exception("Falha inesperada ao validar upload")
        return resposta_erro("Falha interna inesperada.", 500)
    finally:
        arquivo.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
