# ⛓️ DApp Controle de Acesso - Blockchain Lab 4

API REST desenvolvida em **FastAPI** para gerenciamento de perfis de acesso integrados a um Smart Contract na Blockchain Ethereum local (**Anvil**) via **Web3.py**.

---

## 🏗️ Arquitetura do Projeto

```text
blockchain-lab4-dapp/
├── backend/
│   ├── abi/
│   │   └── ControleAcesso.json   # ABI gerada após o build do Solidity
│   ├── api/                      # Routers/Controllers do FastAPI
│   ├── schemas/                  # Modelos Pydantic (Request/Response)
│   ├── services/                 # Regras de Negócio e integração Web3
│   ├── config.py                 # Configurações e leitura do .env
│   ├── main.py                   # Ponto de entrada da API
│   └── requirements.txt          # Dependências Python
├── contracts/
│   └── ControleAcesso.sol        # Smart Contract em Solidity
├── setup.sh                      # Script de build, deploy e geração do .env
└── README.md
```


# 🛠️ 1. Pré-requisitos (Instalação Global)

Caso ainda não tenha o ambiente configurado na sua máquina, instale os pacotes do sistema e o Foundry (necessário para o anvil e forge):
Bash

## 1. Atualizar sistema e instalar pacotes do Python/Build

```bash
sudo apt update && sudo apt install -y build-essential python3-venv python3-pip curl git
````
## 2. Instalar o Foundry (Anvil + Forge)

    curl -L [https://foundry.paradigm.xyz](https://foundry.paradigm.xyz) | bash
    source ~/.bashrc
    foundryup


Verificação: Certifique-se de que anvil --version e forge --version respondem corretamente no terminal.

# 🚀 2. Como Executar o Projeto

Para rodar a aplicação em desenvolvimento, você precisará de 2 terminais abertos simultaneamente.
## 📱 Terminal 1: Nó Blockchain Local (Anvil)

### Inicie a rede Ethereum local simulada:

    anvil

Mantenha este terminal rodando em segundo plano. Ele ficará aguardando o envio de transações.
## 📱 Terminal 2: Deploy dos Contratos + Servidor FastAPI

### A. Configurar o Ambiente Virtual e Dependências Python

Na raiz do projeto, crie e ative seu venv:


    # Criar e ativar ambiente virtual
    python3 -m venv venv
    source venv/bin/activate

#### Instalar pacotes Python
    pip install -r backend/requirements.txt

### B. Compilar, Fazer Deploy e Gerar o .env

Execute o script automatizado para compilar o contrato em Solidity, copiar a ABI gerada e gravar o endereço implantado no .env:


    chmod +x setup.sh
    ./setup.sh

### C. Iniciar a API FastAPI

Com a Anvil rodando e o .env atualizado pelo script, inicie a API:


    fastapi dev backend/main.py

## 🧪 3. Testando a Aplicação

Abra o navegador e acesse a documentação interativa do Swagger UI:
👉 http://127.0.0.1:8000/docs
#### Endpoints Disponíveis:

    POST /acessos/definir-perfil: Atribui ou altera o perfil de uma carteira Ethereum na Blockchain.

    GET /acessos/consultar-perfil/{conta}: Consulta na Blockchain o perfil registrado para o endereço fornecido.

