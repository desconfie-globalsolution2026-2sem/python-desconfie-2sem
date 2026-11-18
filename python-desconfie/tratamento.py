
import re

def normalizar_texto(texto):
    # Padroniza as quebras de linha
    texto = texto.replace("\r\n", "\n").replace("\r", "\n")

    # Remove linhas vazias excessivas
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def remover_espacos_excessivos(texto):
    # Remove espaços repetidos e tabulações
    texto_limpo = re.sub(r"[ \t]+", " ", texto)

    # Remove espaços no início e no final de cada linha
    texto_limpo = re.sub(r"(?m)^ +| +$", "", texto_limpo)

    return texto_limpo.strip()


def tratar_texto(texto):
    texto_sem_espacos = remover_espacos_excessivos(texto)
    texto_normalizado = normalizar_texto(texto_sem_espacos)

    return texto_normalizado
