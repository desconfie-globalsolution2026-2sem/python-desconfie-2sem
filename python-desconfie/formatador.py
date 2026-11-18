LIMITE_CARACTERES_ML = 5000


def validar_campo_ml(valor, nome_campo):
    """Valida uma string antes de enviá-la ao serviço de ML."""
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"O campo '{nome_campo}' deve conter texto não vazio.")
    valor = valor.strip()
    if len(valor) > LIMITE_CARACTERES_ML:
        raise ValueError(
            f"O campo '{nome_campo}' excede o limite de {LIMITE_CARACTERES_ML} caracteres do ML."
        )
    return valor


def formatar_para_ml_texto(texto):
    """Corpo JSON esperado por POST /prever/texto da API de Machine Learning."""
    return {"texto": validar_campo_ml(texto, "texto")}


def formatar_para_ml_url(url):
    """Corpo JSON esperado por POST /prever/url da API de Machine Learning."""
    return {"url": validar_campo_ml(url, "url")}


def formatar_resultado(arquivo_id, nome_arquivo, tipo_arquivo, texto, metodo):
    """Resposta de extração ao Java, mantendo os metadados e o texto tratado.

    O campo entradaMLTexto fornece o corpo exato do POST /prever/texto.
    A classificação de fraude NÃO é realizada aqui.
    """
    entrada_ml = formatar_para_ml_texto(texto)
    return {
        "sucesso": True,
        "arquivoId": arquivo_id,
        "nomeArquivo": nome_arquivo,
        "tipoArquivo": tipo_arquivo,
        "textoExtraido": entrada_ml["texto"],
        "metodoExtracao": metodo,
        "entradaMLTexto": entrada_ml,
    }


if __name__ == "__main__":
    exemplo = formatar_resultado(
        123,
        "mensagem.png",
        "image/png",
        "URGENTE: seu PIX foi bloqueado. Regularize em itau-seguranca.xyz",
        "OCR",
    )
    print("Resultado para o Java:", exemplo)
    print("Corpo para /prever/texto:", formatar_para_ml_texto(exemplo["textoExtraido"]))
    print("Corpo para /prever/url:", formatar_para_ml_url("https://exemplo.com"))