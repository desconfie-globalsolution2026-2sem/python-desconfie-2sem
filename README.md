# DESCONFIE — Módulo Python

**Global Solution FIAP 2026/2 — CitizenTech**  
**Disciplina:** Computational Thinking Using Python  
**Turma:** 1TDSPJ

## Equipe

| Integrante | RM |
|---|---|
| Matheus Matsushita de Souza | 570017 |
| Pedro Amaro Pires | 570636 |
| Juan Souza Marques | 573469 |
| Lucas Leite Carlos | 571985 |

> Confira a grafia dos nomes e os RMs com todos os integrantes antes da entrega.

## 1. Problema e objetivo

Golpes digitais podem chegar por mensagens e documentos que imitam comunicações legítimas, usam linguagem de urgência ou tentam direcionar a vítima a links suspeitos. O **Desconfie** é um projeto de apoio à prevenção de fraudes e à conscientização digital.

O **módulo Python** é responsável por receber arquivos PNG, JPG/JPEG e PDFs, verificar formatos, extrair o texto por OCR ou leitura de PDF, normalizar o conteúdo e estruturá-lo em JSON. Na arquitetura geral do grupo, essa saída é utilizada pela aplicação Java e por um serviço separado de Machine Learning para subsidiar uma análise de risco. A extração de texto **não comprova** que uma mensagem é legítima ou fraudulenta.

## 2. Escopo e arquitetura

Fluxo integrado previsto:

```text
Usuário (interface web)
    -> Java / Spring Boot
    -> Python / Flask (POST /extrair)
    -> validação de arquivo
    -> OCR (imagem) OU extração de texto (PDF)
    -> limpeza e normalização
    -> estruturação em JSON
    -> consulta ao serviço externo de ML (quando configurado)
    -> resposta JSON ao Java
    -> regras de negócio e apresentação ao usuário
```

Há também uma **interface de terminal (`main.py`)** para demonstrar as estruturas de programação estudadas na disciplina. Ela pode ser executada independentemente da API Flask e não precisa de Java nem de `ML_URL` para executar as opções locais de extração e histórico.

**Separação de responsabilidades:** os módulos Python cuidam da ingestão e preparação de dados; os modelos de previsão de fraude e phishing pertencem à disciplina de Artificial Intelligence & Chatbot; Java coordena a aplicação, regras de negócio e integração com o banco de dados.

## 3. Organização dos arquivos

A organização esperada é:

```text
python-desconfie/
├── main.py              # Menu interativo para execução no terminal
├── app.py               # API HTTP Flask
├── ocr.py               # Verificação e OCR de PNG/JPEG
├── pdf_reader.py        # Validação e leitura de PDFs com texto
├── tratamento.py        # Limpeza e normalização textual
├── formatador.py        # Estruturação da saída JSON
├── requirements.txt     # Dependências Python
├── dockerfile           # Ambiente de execução em container (se incluído)
├── dados/
│   └── historico.json   # Criado na primeira gravação pelo main.py
├── identificacao.txt    # Integrantes, RMs e turma (obrigatório no ZIP)
└── README.md            # Este guia
```

O PDF acadêmico da disciplina deve ser incluído no ZIP final. Caso a versão entregue use outros nomes de arquivo, ajuste esta árvore antes de gerar o ZIP.

## 4. Requisitos de ambiente

- Python **3.12 ou superior** é uma escolha compatível com o Dockerfile usado no projeto; confirme a versão com `python --version`.
- Bibliotecas Python declaradas em `requirements.txt` (principalmente `Flask`, `gunicorn`, `Pillow`, `pytesseract`, `pdfplumber` e `requests` no projeto integrado).
- **Tesseract OCR** instalado no sistema, com o pacote do idioma **português (`por`)**, para analisar imagens.
- Acesso à internet **somente para as chamadas a APIs externas**, caso a API Flask esteja configurada para consultar o ML.

### Instalação das bibliotecas

Execute na pasta onde se encontram `requirements.txt`, `main.py` e `app.py`:

```bash
python -m pip install -r requirements.txt
```

### Verificar o OCR

```bash
tesseract --version
tesseract --list-langs
```

A lista de idiomas deve incluir `por`. No Windows, instale o Tesseract e configure seu executável no `PATH`, se necessário. No container Docker do projeto, o Tesseract e o idioma português são instalados pelo arquivo de build.

## 5. Executar pelo terminal — `main.py`

```bash
python main.py
```

O menu acadêmico oferece as seguintes opções, **desde que a versão final de `main.py` esteja presente no ZIP**:

```text
1 - Analisar imagem ou PDF
2 - Tratar mensagem digitada
3 - Historico e estatisticas
4 - Sobre o sistema
0 - Encerrar
```

### 5.1. Análise de imagem ou PDF

Escolha a opção `1` e informe o caminho de um arquivo local, por exemplo:

```text
C:\\Users\\Usuario\\Downloads\\mensagem.png
```

O programa valida o arquivo, utiliza `ocr.py` para imagens ou `pdf_reader.py` para PDFs, aplica `tratamento.py`, gera um registro estruturado com `formatador.py` e armazena o resultado no histórico JSON.

### 5.2. Tratamento manual de mensagem

Escolha a opção `2`, digite ou cole o texto e finalize com `FIM` em uma linha separada. O conteúdo será normalizado e salvo no histórico.

### 5.3. Histórico e estatísticas

Escolha a opção `3` para listar registros, pesquisar por ID, visualizar contagens ou limpar o histórico mediante confirmação.

### Persistência

O terminal grava registros em `dados/historico.json`, criado na primeira gravação. O arquivo permite consultar análises de execuções anteriores. Não inclua mensagens ou documentos com senhas, códigos de autenticação, dados bancários ou informações pessoais reais nos exemplos de entrega.

## 6. Executar a API Flask — `app.py`

Em ambiente local:

```bash
python app.py
```

Com a configuração do código desenvolvido, o Flask inicia na porta `5000` quando `PORT` não é definida. Para verificar a inicialização, acesse:

```text
http://localhost:5000/health
```

Na publicação do projeto, o serviço Python foi preparado para executar em container Docker com Gunicorn.

### Variável de ambiente para ML

A versão integrada de `app.py` utiliza a variável de ambiente **`ML_URL`** como endereço base da API desenvolvida pela equipe de IA. Exemplo ilustrativo:

```text
ML_URL=https://endereco-real-da-api-ml
```

Ela deve apontar para o **serviço de ML publicado**, não para o GitHub nem para a própria API Python. O aplicativo monta os caminhos `/prever/texto` e `/prever/url` ao realizar as requisições. A ausência ou indisponibilidade desse serviço impede as previsões na versão integrada.

## 7. Endpoints da API

Os exemplos seguintes descrevem o contrato da versão integrada de `app.py`; devem ser validados em teste com o código efetivamente entregue.

| Método | Endpoint | Entrada | Finalidade |
|---|---|---|---|
| GET | `/health` | Sem corpo | Verificar se o Flask responde e se `ML_URL` está configurada |
| POST | `/extrair` | `multipart/form-data`, campo `arquivo` obrigatório e `arquivoId` opcional | Validar arquivo, extrair e tratar o texto e consultar ML quando configurado |
| POST | `/prever/texto` | JSON com `texto` | Encaminhar texto à API de ML |
| POST | `/prever/url` | JSON com `url` | Encaminhar URL à API de ML |

**Exemplo de envio para `/extrair` (com cURL):**

```bash
curl -X POST http://localhost:5000/extrair -F "arquivo=@teste.png" -F "arquivoId=1"
```

**Exemplo da entrada de previsão textual:**

```json
{"texto": "Mensagem de teste para avaliacao de risco"}
```

**Exemplo de campos da saída de extração (ilustrativo):**

```json
{
  "sucesso": true,
  "arquivoId": 1,
  "nomeArquivo": "teste.png",
  "tipoArquivo": "image/png",
  "textoExtraido": "Mensagem de teste",
  "metodoExtracao": "OCR"
}
```

A versão integrada pode acrescentar `analiseML`, `textoTruncadoParaML` e `entradaMLTexto`. As probabilidades devolvidas pela IA não constituem garantia de autenticidade ou fraude.

## 8. Critérios de Computational Thinking demonstrados pelo terminal

| Critério acadêmico | Aplicação prevista no `main.py` |
|---|---|
| Menus e submenus | Menu principal e submenu de histórico |
| Entrada e saída / f-strings | `input()` e mensagens formatadas ao usuário |
| `match-case` | Seleção de opções dos menus |
| `if-elif-else` | Tratamento de tipos de arquivo e confirmações |
| `while` e `for` | Navegação, coleta de texto e listagem de registros |
| Listas | Linhas digitadas e histórico de análises |
| Tuplas | Tipos de arquivo apresentados no menu |
| Strings | Conteúdo extraído e normalização |
| Dicionários | Registros estruturados e contagens |
| Sets | Extensões permitidas e métodos de extração |
| Funções com parâmetros e retorno | Validação, extração, formatação e persistência |
| Persistência | Arquivo `dados/historico.json` |
| Usabilidade | Mensagens de instrução, validação e erro |

**Restrições da disciplina:** não utilizar classes/orientação a objetos próprias nem *list comprehensions* no código submetido. Revise todos os arquivos `.py` entregues, além do `main.py`. Esta tabela descreve a estrutura proposta e não substitui os testes no ambiente do professor.

## 9. Testes recomendados antes da entrega

1. Iniciar `main.py`, navegar nos dois menus e encerrar sem erros.
2. Analisar uma imagem PNG/JPEG legível e verificar o texto retornado.
3. Analisar um PDF que contenha texto selecionável e verificar sua extração.
4. Digitar uma mensagem manualmente e conferir a normalização.
5. Fechar e reabrir o programa; consultar os registros persistidos em JSON.
6. Informar arquivo inexistente, formato inválido e entrada vazia para verificar mensagens de erro.
7. Se utilizar a integração online, testar `/health`, `/prever/texto`, `/prever/url` e `/extrair`.

**Limitações importantes:** `pdfplumber` extrai texto de PDFs digitais; um PDF exclusivamente escaneado pode não produzir texto sem OCR das páginas. O OCR pode apresentar erros conforme qualidade da imagem, contraste ou idioma. A API depende da disponibilidade do serviço de ML para devolver previsões na versão integrada.

## 10. Registro de uso de inteligência artificial

A IA generativa **ChatGPT (OpenAI)** foi usada como apoio à explicação de conceitos, planejamento da integração entre módulos, revisão de código, organização do menu acadêmico, preparação de documentação e sugestões de testes. Foram discutidos, entre outros tópicos, o uso de `Flask`, o tratamento de arquivos, o OCR, a comunicação com os serviços de Java e ML e a estruturação dos resultados JSON.

**Revisão crítica exigida:** o grupo deve inspecionar, compreender, testar e adaptar quaisquer sugestões aproveitadas. A aplicação deve ser avaliada pelo código realmente entregue, e não por funcionalidades apenas descritas. Confirme com os demais integrantes se outras ferramentas de IA foram utilizadas e acrescente-as aqui, com seus usos efetivos.

**Exemplos de solicitações que orientaram o trabalho** (descrições resumidas, não transcrições literais):

- Explicar o papel de `ocr.py`, `pdf_reader.py` e `tratamento.py` no processamento de arquivos.
- Orientar a implementação dos endpoints Flask para extração e integração com os modelos de ML.
- Criar uma interface de terminal com menu, estruturas de decisão, repetição e persistência JSON alinhada aos requisitos da disciplina.
- Revisar instruções de Docker, Tesseract e publicação em serviço web.

## 11. Conteúdo obrigatório do ZIP

Conforme o enunciado oficial da FIAP, a entrega de Computational Thinking Using Python exige:

- Arquivos-fonte **`.py`**, incluindo os módulos necessários para execução.
- **Documentação e guia de execução em PDF** (o README não substitui este documento).
- **Arquivo `.txt` com nome completo, RM e turma de todos os integrantes**.

Este `README.md` é **complementar e opcional**. Se incluir `requirements.txt` e o arquivo de configuração Docker, confirme que o ZIP continua organizado e que o código pode ser executado com as instruções fornecidas. Não inclua `.env`, credenciais, senhas, tokens nem dados reais sensíveis.

**Prazo de envio:** 19/11/2026, até 23h55, via Portal do Aluno.  
**Apresentação presencial:** entre 23 e 27/11/2026, conforme organização do professor.

## 12. Observações finais

O módulo Python demonstra conceitos de programação procedural por meio de uma interface de terminal e disponibiliza uma API HTTP para a arquitetura integrada do Desconfie. Os resultados automatizados devem ser entendidos como apoio à prevenção e conscientização, nunca como confirmação definitiva de que um conteúdo é seguro.

**Antes de entregar:** confira se os nomes dos arquivos, endpoints, exemplos de resposta e funcionalidades deste README correspondem exatamente ao código incluído no ZIP.
