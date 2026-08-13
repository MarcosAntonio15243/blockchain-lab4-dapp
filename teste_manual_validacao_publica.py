import os
import sys

import requests
from eth_account import Account
from eth_account.messages import encode_defunct

BASE_URL = "http://localhost:8000/api/v1"

CHAVE_ADMIN = os.environ.get("ADMIN_PRIVATE_KEY")
if not CHAVE_ADMIN:
    print("Defina ADMIN_PRIVATE_KEY antes de rodar.")
    sys.exit(1)

admin = Account.from_key(CHAVE_ADMIN)


def logar(conta) -> str:
    resposta_nonce = requests.post(f"{BASE_URL}/auth/nonce", json={"endereco": conta.address}, timeout=10)
    resposta_nonce.raise_for_status()
    mensagem = resposta_nonce.json()["mensagem"]

    assinatura = Account.sign_message(encode_defunct(text=mensagem), private_key=conta.key)

    resposta = requests.post(
        f"{BASE_URL}/auth/verificar",
        json={"endereco": conta.address, "assinatura": assinatura.signature.hex()},
        timeout=10,
    )
    resposta.raise_for_status()
    resultado = resposta.json()
    if not resultado["autenticado"]:
        raise RuntimeError("Falha ao autenticar admin")
    return resultado["token"]


def cabecalho(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


print("Autenticando como Vara (admin)...")
token = logar(admin)
print("✅ Autenticado.\n")

print("1) Registrando alvará de viagem on-chain...")
resposta = requests.post(
    f"{BASE_URL}/documentos",
    json={
        "hashDocumento": "0x" + "cc" * 32,
        "tipoDocumento": "Alvará de Autorização de Viagem",
        "orgaoEmissor": "2ª Vara da Infância e Juventude de Campina Grande",
        "autoridadeSignataria": "Dra. Maria Exemplo, Juíza de Direito",
    },
    headers=cabecalho(token),
    timeout=10,
)
resposta.raise_for_status()

# Pega o doc_id do documento recem-criado
resposta_lista = requests.get(f"{BASE_URL}/documentos", headers=cabecalho(token), timeout=10)
documentos = resposta_lista.json()
doc_id = documentos[-1].get("docId") or documentos[-1].get("doc_id")
print(f"   doc_id: {doc_id}\n")

print("2) Cadastrando dados sensíveis (nome, acompanhante, destino)...")
resposta = requests.post(
    f"{BASE_URL}/documentos/{doc_id}/dados-sensiveis",
    json={
        "docId": doc_id,
        "categoria": "alvara_viagem",
        "nomeCrianca": "João da Silva Exemplo",
        "nomeAcompanhante": "Maria da Silva Exemplo (mãe)",
        "destinoViagem": "Recife/PE",
    },
    headers=cabecalho(token),
    timeout=10,
)
print(f"   status={resposta.status_code} corpo={resposta.json()}\n")
resposta.raise_for_status()

print("3) Gerando/lendo PDF de teste e anexando ao documento...")
CAMINHO_PDF_TESTE = "documento_exemplo.pdf"
if not os.path.exists(CAMINHO_PDF_TESTE):
    print(f"   {CAMINHO_PDF_TESTE} não encontrado, gerando um PDF mínimo de teste...")
    with open(CAMINHO_PDF_TESTE, "wb") as arquivo_novo:
        arquivo_novo.write(b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>")

with open(CAMINHO_PDF_TESTE, "rb") as arquivo_pdf:
    resposta = requests.post(
        f"{BASE_URL}/documentos/{doc_id}/arquivo",
        files={"arquivo": ("alvara.pdf", arquivo_pdf, "application/pdf")},
        headers=cabecalho(token),
        timeout=10,
    )
print(f"   status={resposta.status_code} corpo={resposta.json()}")
resposta.raise_for_status()

print("\n4) Baixando o PDF de volta (confirma que o download autenticado funciona)...")
resposta = requests.get(f"{BASE_URL}/documentos/{doc_id}/arquivo", headers=cabecalho(token), timeout=10)
resposta.raise_for_status()
with open("baixado.pdf", "wb") as saida:
    saida.write(resposta.content)
print(f"   PDF salvo em baixado.pdf ({len(resposta.content)} bytes)")

print("\n5) Consultando a rota PÚBLICA de validação (sem autenticação, como no QR Code)...")
url_validacao = f"{BASE_URL}/validacao/{doc_id}"
resposta = requests.get(url_validacao, timeout=10)  # nota: sem headers de auth, de proposito
print(f"   status={resposta.status_code}")
resposta.raise_for_status()
dados_publicos = resposta.json()
for chave, valor in dados_publicos.items():
    print(f"   {chave}: {valor}")

print("\n" + "=" * 70)
print("PRONTO! Documento de teste criado e validado publicamente.")
print(f"URL de validação pública: {url_validacao}")
print(f"doc_id (código de validação): {doc_id}")
print("=" * 70)

# Salva num arquivo para a pagina HTML usar
with open("doc_id_teste.txt", "w") as f:
    f.write(doc_id)