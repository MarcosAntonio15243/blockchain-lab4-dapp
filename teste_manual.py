# teste_manual_auth.py
import requests
from eth_account import Account
from eth_account.messages import encode_defunct

BASE_URL = "http://localhost:8000/api/v1"

# 1. Cria uma carteira de teste (em produção seria MetaMask etc.)
conta_teste = Account.create()
endereco = conta_teste.address
print(f"Endereco de teste: {endereco}")

# 2. Pede o nonce/mensagem para assinar
resposta_nonce = requests.post(f"{BASE_URL}/auth/nonce", json={"endereco": endereco})
print(f"Status: {resposta_nonce.status_code}")
print(f"Corpo: {resposta_nonce.json()}")

mensagem = resposta_nonce.json()["mensagem"]

# 3. Assina a mensagem com a chave privada (isso que a carteira faria)
mensagem_codificada = encode_defunct(text=mensagem)
assinatura = Account.sign_message(mensagem_codificada, private_key=conta_teste.key)

# 4. Envia a assinatura para verificação
resposta_verificacao = requests.post(
    f"{BASE_URL}/auth/verificar",
    json={"endereco": endereco, "assinatura": assinatura.signature.hex()},
)
resultado = resposta_verificacao.json()
print(f"Resultado da verificacao: {resultado}")

if resultado["autenticado"]:
    token = resultado["token"]

    # 5. Usa o token numa rota protegida
    resposta_protegida = requests.get(
        f"{BASE_URL}/documentos",
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"Status rota protegida: {resposta_protegida.status_code}")
    print(resposta_protegida.json())