"""Ponto de entrada WSGI alternativo para provedores de hospedagem."""

"""Desconfie - Interface de terminal para Computational Thinking Using Python."""

import json
from datetime import datetime
from pathlib import Path

from ocr import validar_imagem, extrair_texto_imagem
from pdf_reader import validar_pdf, extrair_texto_pdf
from tratamento import tratar_texto
from formatador import formatar_resultado


# Configuracoes do sistema
ARQUIVO_HISTORICO = Path("dados/historico.json")
LIMITE_ARQUIVO = 10 * 1024 * 1024

EXTENSOES_IMAGEM = {"png", "jpg", "jpeg"}
EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg", "pdf"}

TIPOS_ARQUIVO = ("Imagem PNG", "Imagem JPEG", "Documento PDF")


def exibir_cabecalho(titulo):
    """Exibe o titulo da secao no terminal."""
    print("\n" + "=" * 55)
    print(f" DESCONFIE | {titulo}")
    print("=" * 55)


def pausar():
    """Aguarda o usuario antes de voltar ao menu."""
    input("\nPressione ENTER para continuar...")


def carregar_historico():
    """Carrega os registros salvos em JSON."""
    ARQUIVO_HISTORICO.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not ARQUIVO_HISTORICO.exists():
        return []

    try:
        with open(
            ARQUIVO_HISTORICO,
            "r",
            encoding="utf-8"
        ) as arquivo:
            dados = json.load(arquivo)

        if isinstance(dados, list):
            return dados

        print("Historico invalido. Esperava-se uma lista.")
        return []

    except (OSError, json.JSONDecodeError) as erro:
        print(f"Erro ao carregar historico: {erro}")
        return []


def salvar_historico(historico):
    """Persiste a lista de analises em arquivo JSON."""
    ARQUIVO_HISTORICO.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        ARQUIVO_HISTORICO,
        "w",
        encoding="utf-8"
    ) as arquivo:
        json.dump(
            historico,
            arquivo,
            ensure_ascii=False,
            indent=4
        )


def gerar_id(historico):
    """Gera um identificador sequencial para cada analise."""
    maior_id = 0

    for registro in historico:
        identificador = registro.get("arquivoId")

        if isinstance(identificador, int):
            if identificador > maior_id:
                maior_id = identificador

    return maior_id + 1


def identificar_tipo(conteudo, extensao):
    """Verifica se o conteudo corresponde a extensao."""
    if extensao == "png":
        if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"

    elif extensao == "jpg" or extensao == "jpeg":
        if conteudo.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"

    elif extensao == "pdf":
        if conteudo.startswith(b"%PDF-"):
            return "application/pdf"

    return None


def extrair_conteudo(caminho):
    """Valida o arquivo e executa o modulo de extracao."""
    arquivo = Path(caminho.strip().strip('"'))

    if not arquivo.is_file():
        raise ValueError("Arquivo nao encontrado.")

    extensao = arquivo.suffix.lower().lstrip(".")

    if extensao not in EXTENSOES_PERMITIDAS:
        raise ValueError(
            f"Extensao .{extensao} nao permitida."
        )

    if arquivo.stat().st_size > LIMITE_ARQUIVO:
        raise ValueError("Arquivo excede o limite de 10 MB.")

    conteudo = arquivo.read_bytes()

    if not conteudo:
        raise ValueError("O arquivo esta vazio.")

    tipo = identificar_tipo(conteudo, extensao)

    if tipo is None:
        raise ValueError(
            "A extensao nao corresponde ao conteudo."
        )

    if extensao in EXTENSOES_IMAGEM:
        if not validar_imagem(conteudo):
            raise ValueError("Imagem invalida ou corrompida.")

        texto = extrair_texto_imagem(conteudo)
        metodo = "OCR"

    elif extensao == "pdf":
        if not validar_pdf(conteudo):
            raise ValueError("Documento PDF invalido.")

        texto = extrair_texto_pdf(conteudo)
        metodo = "PDF_TEXTO"

    else:
        raise ValueError("Tipo de arquivo nao reconhecido.")

    return texto, tipo, metodo, arquivo.name


def criar_registro(
    historico,
    nome,
    tipo,
    texto,
    metodo
):
    """Formata a analise para o sistema e adiciona metadados."""
    identificador = gerar_id(historico)

    resultado = formatar_resultado(
        identificador,
        nome,
        tipo,
        texto,
        metodo
    )

    resultado["dataAnalise"] = datetime.now().isoformat(
        timespec="seconds"
    )

    return resultado


def registrar_analise(resultado):
    """Armazena permanentemente uma analise."""
    historico = carregar_historico()
    historico.append(resultado)
    salvar_historico(historico)


def mostrar_resultado(resultado):
    """Exibe os dados da extracao no terminal."""
    print("\n--- RESULTADO DA EXTRACAO ---")

    print(f"ID: {resultado['arquivoId']}")
    print(f"Arquivo: {resultado['nomeArquivo']}")
    print(f"Tipo: {resultado['tipoArquivo']}")
    print(f"Metodo: {resultado['metodoExtracao']}")
    print(f"Data: {resultado['dataAnalise']}")

    texto = resultado["textoExtraido"]

    print(f"\nTexto extraido ({len(texto)} caracteres):")
    print("-" * 45)
    print(texto)
    print("-" * 45)

    print("\nO texto foi preparado para analise pelo ML.")
    print("Este menu nao realiza a classificacao de golpes.")


def analisar_arquivo():
    """Executa o fluxo de imagens e PDFs pelo terminal."""
    exibir_cabecalho("ANALISAR ARQUIVO")

    print("Formatos permitidos:")

    for formato in TIPOS_ARQUIVO:
        print(f" - {formato}")

    caminho = input("\nDigite o caminho do arquivo: ").strip()

    if not caminho:
        print("Caminho nao informado.")
        return

    try:
        texto, tipo, metodo, nome = extrair_conteudo(caminho)

        texto_tratado = tratar_texto(texto)

        if not texto_tratado:
            print("Nenhum texto foi identificado.")
            return

        historico = carregar_historico()

        resultado = criar_registro(
            historico,
            nome,
            tipo,
            texto_tratado,
            metodo
        )

        registrar_analise(resultado)
        mostrar_resultado(resultado)

        print("\nAnalise salva no historico JSON.")

    except (ValueError, RuntimeError, OSError) as erro:
        print(f"\nErro na analise: {erro}")


def analisar_texto_manual():
    """Permite testar o tratamento sem enviar um arquivo."""
    exibir_cabecalho("TRATAR TEXTO")

    print("Cole uma mensagem suspeita.")
    print("Finalize digitando FIM em uma linha separada.\n")

    linhas = []

    while True:
        linha = input()

        if linha.strip().upper() == "FIM":
            break

        linhas.append(linha)

    texto_original = "\n".join(linhas)

    if not texto_original.strip():
        print("Nenhum texto foi informado.")
        return

    texto_tratado = tratar_texto(texto_original)

    historico = carregar_historico()

    resultado = criar_registro(
        historico,
        "entrada_manual.txt",
        "text/plain",
        texto_tratado,
        "ENTRADA_MANUAL"
    )

    registrar_analise(resultado)
    mostrar_resultado(resultado)

    print("\nTexto salvo no historico JSON.")


def listar_historico():
    """Mostra todos os registros existentes."""
    exibir_cabecalho("HISTORICO")

    historico = carregar_historico()

    if not historico:
        print("Nenhuma analise registrada.")
        return

    for registro in historico:
        print(f"\nID: {registro.get('arquivoId')}")
        print(f"Arquivo: {registro.get('nomeArquivo')}")
        print(f"Metodo: {registro.get('metodoExtracao')}")
        print(f"Data: {registro.get('dataAnalise')}")
        print("-" * 45)

    print(f"\nTotal de registros: {len(historico)}")


def buscar_registro():
    """Pesquisa um registro utilizando seu identificador."""
    exibir_cabecalho("BUSCAR ANALISE")

    entrada = input("Digite o ID da analise: ").strip()

    if not entrada.isdigit():
        print("Informe um ID numerico.")
        return

    identificador = int(entrada)
    historico = carregar_historico()
    encontrado = None

    for registro in historico:
        if registro.get("arquivoId") == identificador:
            encontrado = registro
            break

    if encontrado is None:
        print(f"Nenhuma analise encontrada com ID {identificador}.")
        return

    mostrar_resultado(encontrado)


def mostrar_estatisticas():
    """Conta arquivos e metodos usados nas extracoes."""
    exibir_cabecalho("ESTATISTICAS")

    historico = carregar_historico()

    if not historico:
        print("Nao existem dados para estatisticas.")
        return

    metodos = set()
    contagens = {}
    total_caracteres = 0

    for registro in historico:
        metodo = registro.get("metodoExtracao", "DESCONHECIDO")
        texto = registro.get("textoExtraido", "")

        metodos.add(metodo)
        total_caracteres += len(texto)

        if metodo in contagens:
            contagens[metodo] += 1
        else:
            contagens[metodo] = 1

    print(f"Total de analises: {len(historico)}")
    print(f"Caracteres processados: {total_caracteres}")
    print(f"Metodos diferentes: {len(metodos)}")

    print("\nAnalises por metodo:")

    for metodo, quantidade in contagens.items():
        print(f" - {metodo}: {quantidade}")


def limpar_historico():
    """Limpa o historico somente com confirmacao do usuario."""
    exibir_cabecalho("LIMPAR HISTORICO")

    confirmacao = input(
        "Deseja apagar todas as analises? (SIM/NAO): "
    ).strip().upper()

    if confirmacao == "SIM":
        salvar_historico([])
        print("Historico apagado com sucesso.")

    elif confirmacao == "NAO":
        print("Operacao cancelada.")

    else:
        print("Resposta invalida. Nenhum dado foi apagado.")


def menu_historico():
    """Submenu de consultas e gerenciamento."""
    while True:
        exibir_cabecalho("GERENCIAR HISTORICO")

        print("1 - Listar analises")
        print("2 - Buscar analise por ID")
        print("3 - Visualizar estatisticas")
        print("4 - Limpar historico")
        print("0 - Voltar ao menu principal")

        opcao = input("\nEscolha uma opcao: ").strip()

        match opcao:
            case "1":
                listar_historico()
                pausar()

            case "2":
                buscar_registro()
                pausar()

            case "3":
                mostrar_estatisticas()
                pausar()

            case "4":
                limpar_historico()
                pausar()

            case "0":
                return

            case _:
                print("Opcao invalida.")
                pausar()


def mostrar_sobre():
    """Apresenta o projeto e as responsabilidades do Python."""
    exibir_cabecalho("SOBRE O DESCONFIE")

    print("Projeto: Desconfie")
    print("Global Solution 2026/2 - CitizenTech")
    print("Disciplina: Computational Thinking Using Python")

    print("\nObjetivo:")
    print(
        "Extrair e preparar textos de mensagens suspeitas "
        "para apoiar a identificacao de golpes digitais."
    )

    print("\nModulos:")
    print("ocr.py - Reconhecimento de texto em imagens")
    print("pdf_reader.py - Extracao de texto de PDFs")
    print("tratamento.py - Limpeza e normalizacao")
    print("formatador.py - Estruturacao dos resultados")
    print("app.py - API de integracao")
    print("main.py - Interface de terminal")

    print("\nO modelo de Machine Learning pertence")
    print("a outro modulo do projeto Desconfie.")


def menu_principal():
    """Controla o fluxo principal usando while e match-case."""
    while True:
        exibir_cabecalho("MENU PRINCIPAL")

        print("1 - Analisar imagem ou PDF")
        print("2 - Tratar mensagem digitada")
        print("3 - Historico e estatisticas")
        print("4 - Sobre o sistema")
        print("0 - Encerrar")

        opcao = input("\nEscolha uma opcao: ").strip()

        match opcao:
            case "1":
                analisar_arquivo()
                pausar()

            case "2":
                analisar_texto_manual()
                pausar()

            case "3":
                menu_historico()

            case "4":
                mostrar_sobre()
                pausar()

            case "0":
                print("\nEncerrando Desconfie. Ate logo!")
                break

            case _:
                print("Opcao invalida. Tente novamente.")
                pausar()


if __name__ == "__main__":
    menu_principal()

from app import app


if __name__ == "__main__":
    app.run()
