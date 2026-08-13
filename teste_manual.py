import os
import requests
from eth_account import Account

from eth_account.messages import encode_defunct

BASE_URL = "http://localhost:8000/api/v1"

# 1. Cria uma carteira de teste (em produção seria MetaMask etc.)
# conta_teste = Account.create()
conta_teste = Account.from_key(os.environ["CHAVE_PRIVADA_ADMIN"])
conta_usuario = Account.create()
endereco = conta_teste.address
endereco_usuario = conta_usuario.address
print(f"Endereco de teste: {endereco}")
print(f"Endereco de usuario: {endereco_usuario}")

# 2. Pede o nonce/mensagem para assinar
resposta_nonce = requests.post(f"{BASE_URL}/auth/nonce", json={"endereco": endereco})
print(f"Status: {resposta_nonce.status_code}")
print(f"Corpo: {resposta_nonce.json()}")

mensagem = resposta_nonce.json()["mensagem"]

nonce_usuario = requests.post(f"{BASE_URL}/auth/nonce", json={"endereco": endereco_usuario})
print(f"Status: {nonce_usuario.status_code}")
print(f"Corpo: {nonce_usuario.json()}")

mensagem_usuario = nonce_usuario.json()["mensagem"]

# 3. Assina a mensagem com a chave privada (isso que a carteira faria)
mensagem_codificada = encode_defunct(text=mensagem)
assinatura = Account.sign_message(mensagem_codificada, private_key=conta_teste.key)

mensagem_codificada_usuario = encode_defunct(text=mensagem_usuario)
assinatura_usuario = Account.sign_message(mensagem_codificada_usuario, private_key=conta_usuario.key)

# 4. Envia a assinatura para verificação
resposta_verificacao = requests.post(
    f"{BASE_URL}/auth/verificar",
    json={"endereco": endereco, "assinatura": assinatura.signature.hex()},
)

resultado = resposta_verificacao.json()
print(f"Resultado da verificacao: {resultado}")

resposta_nonce_usuario = requests.post(
    f"{BASE_URL}/auth/verificar",
    json={"endereco": endereco_usuario, "assinatura": assinatura_usuario.signature.hex()},
)
resultado_usuario = resposta_nonce_usuario.json()
print(f"Resultado da verificacao do usuario: {resultado_usuario}")

if resultado["autenticado"]:
    token = resultado["token"]

    # 5. Usa o token numa rota protegida
    resposta_protegida = requests.get(
        f"{BASE_URL}/documentos",
        headers={"Authorization": f"Bearer {token}"},
    )
    print(f"Status rota protegida: {resposta_protegida.status_code}")
    print(resposta_protegida.json())

if resultado_usuario["autenticado"]:
    token_usuario = resultado_usuario["token"]

    resposta_protegida_usuario = requests.get(
        f"{BASE_URL}/documentos",
        headers={"Authorization": f"Bearer {token_usuario}"},
    )
    print(f"Status rota protegida usuario: {resposta_protegida_usuario.status_code}")
    print(resposta_protegida_usuario.json())    


print()
print("\nToken Vara" + token)
print("\nToken Usuario" + token_usuario)