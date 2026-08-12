import os
import sys
import time
from datetime import datetime, timedelta, timezone

import requests
from eth_account import Account
from eth_account.messages import encode_defunct

BASE_URL = "http://localhost:8000/api/v1"

CHAVE_ADMIN = os.environ.get("ADMIN_PRIVATE_KEY")
if not CHAVE_ADMIN:
    print("Defina a variavel de ambiente ADMIN_PRIVATE_KEY antes de rodar (mesma chave do CHAVE_PRIVADA_ADMIN).")
    sys.exit(1)

PERFIL_POLICIA_FEDERAL = 2  # espelha o enum Perfil do ControleAcesso.sol


def logar(conta) -> str:
    """Executa o fluxo completo de login (nonce -> assinatura -> token) e devolve o token."""
    resposta_nonce = requests.post(f"{BASE_URL}/auth/nonce", json={"endereco": conta.address})
    resposta_nonce.raise_for_status()
    mensagem = resposta_nonce.json()["mensagem"]

    assinatura = Account.sign_message(encode_defunct(text=mensagem), private_key=conta.key)

    resposta_verificacao = requests.post(
        f"{BASE_URL}/auth/verificar",
        json={"endereco": conta.address, "assinatura": assinatura.signature.hex()},
    )
    resposta_verificacao.raise_for_status()
    resultado = resposta_verificacao.json()

    if not resultado["autenticado"]:
        raise RuntimeError(f"Falha ao autenticar {conta.address}")

    return resultado["token"]


def cabecalho(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def esperar(segundos: float, motivo: str):
    print(f"   (aguardando {segundos:.0f}s: {motivo})")
    time.sleep(segundos)


# ---------------------------------------------------------------------------
# Setup: conta admin (Vara) e conta de teste (vai virar Policia Federal)
# ---------------------------------------------------------------------------

admin = Account.from_key(CHAVE_ADMIN)
policia_federal = Account.create()

print(f"Admin (Vara):       {admin.address}")
print(f"Policia Federal:    {policia_federal.address}\n")

token_admin = logar(admin)
print("✅ Admin autenticado.\n")

# ---------------------------------------------------------------------------
# 1. Atribui o perfil PoliciaFederal a conta de teste
# ---------------------------------------------------------------------------

print("1) Atribuindo perfil PoliciaFederal a conta de teste...")
resposta = requests.post(
    f"{BASE_URL}/acessos/definir-perfil",
    json={"conta": policia_federal.address, "perfil": PERFIL_POLICIA_FEDERAL},
    headers=cabecalho(token_admin),
)
print(f"   status={resposta.status_code} corpo={resposta.json()}")
assert resposta.status_code == 200, "Falha ao definir perfil"

token_policia = logar(policia_federal)
print("✅ Conta Policia Federal autenticada.\n")

# ---------------------------------------------------------------------------
# 2. Vara registra um documento de teste
# ---------------------------------------------------------------------------

print("2) Registrando documento de teste...")
resposta = requests.post(
    f"{BASE_URL}/documentos",
    json={
        "hashDocumento": "0x" + "aa" * 32,
        "tipoDocumento": "alvara de viagem",
        "orgaoEmissor": "Vara da Infancia",
        "autoridadeSignataria": "Juiz de Teste",
    },
    headers=cabecalho(token_admin),
)
print(f"   status={resposta.status_code} corpo={resposta.json()}")
assert resposta.status_code == 200, "Falha ao registrar documento"

# Precisamos do doc_id: listamos os documentos e pegamos o ultimo registrado
resposta = requests.get(f"{BASE_URL}/documentos", headers=cabecalho(token_admin))
documentos = resposta.json()
assert documentos, "Nenhum documento encontrado apos o registro"
doc_id = documentos[-1]["docId"] if "docId" in documentos[-1] else documentos[-1]["doc_id"]
print(f"   doc_id: {doc_id}\n")

# ---------------------------------------------------------------------------
# 3. SEM permissao concedida: Policia Federal tenta ler -> deve ser 403
# ---------------------------------------------------------------------------

print("3) Tentando ler documento SEM permissao concedida (esperado: 403)...")
resposta = requests.get(f"{BASE_URL}/documentos/{doc_id}", headers=cabecalho(token_policia))
print(f"   status={resposta.status_code} corpo={resposta.json()}")
assert resposta.status_code == 403, f"Esperava 403, veio {resposta.status_code}"
print("✅ Bloqueado corretamente.\n")

# ---------------------------------------------------------------------------
# 4. Vara concede permissao de leitura (sem expiracao) -> deve liberar
# ---------------------------------------------------------------------------

print("4) Concedendo permissao de leitura (sem expiracao)...")
resposta = requests.post(
    f"{BASE_URL}/permissoes",
    json={"docId": doc_id, "perfil": "PoliciaFederal"},
    headers=cabecalho(token_admin),
)
print(f"   status={resposta.status_code} corpo={resposta.json()}")
assert resposta.status_code == 200, "Falha ao conceder permissao"
permissao_id = resposta.json()["id"]

print("   Tentando ler novamente (esperado: 200)...")
resposta = requests.get(f"{BASE_URL}/documentos/{doc_id}", headers=cabecalho(token_policia))
print(f"   status={resposta.status_code}")
assert resposta.status_code == 200, f"Esperava 200, veio {resposta.status_code}: {resposta.text}"
print("✅ Leitura liberada apos concessao.\n")

# ---------------------------------------------------------------------------
# 5. Revogando a permissao -> deve voltar a bloquear
# ---------------------------------------------------------------------------

print("5) Revogando a permissao concedida...")
resposta = requests.delete(
    f"{BASE_URL}/permissoes",
    json={"permissaoId": permissao_id},
    headers=cabecalho(token_admin),
)
print(f"   status={resposta.status_code} corpo={resposta.json()}")
assert resposta.status_code == 200, "Falha ao revogar permissao"

print("   Tentando ler apos revogacao (esperado: 403)...")
resposta = requests.get(f"{BASE_URL}/documentos/{doc_id}", headers=cabecalho(token_policia))
print(f"   status={resposta.status_code}")
assert resposta.status_code == 403, f"Esperava 403, veio {resposta.status_code}"
print("✅ Bloqueado corretamente apos revogacao.\n")

# ---------------------------------------------------------------------------
# 6. Permissao com tempo limite curto -> deve expirar sozinha
# ---------------------------------------------------------------------------

print("6) Concedendo permissao com expiracao em 5 segundos...")
expira_em = (datetime.now(timezone.utc) + timedelta(seconds=5)).isoformat()
resposta = requests.post(
    f"{BASE_URL}/permissoes",
    json={"docId": doc_id, "perfil": "PoliciaFederal", "expiraEm": expira_em},
    headers=cabecalho(token_admin),
)
print(f"   status={resposta.status_code} corpo={resposta.json()}")
assert resposta.status_code == 200, "Falha ao conceder permissao com prazo"

print("   Lendo imediatamente (esperado: 200, ainda dentro do prazo)...")
resposta = requests.get(f"{BASE_URL}/documentos/{doc_id}", headers=cabecalho(token_policia))
print(f"   status={resposta.status_code}")
assert resposta.status_code == 200, f"Esperava 200, veio {resposta.status_code}"
print("✅ Leitura liberada dentro do prazo.\n")

esperar(6, "esperando o prazo de 5s expirar")

print("   Lendo apos o prazo expirar (esperado: 403)...")
resposta = requests.get(f"{BASE_URL}/documentos/{doc_id}", headers=cabecalho(token_policia))
print(f"   status={resposta.status_code}")
assert resposta.status_code == 403, f"Esperava 403, veio {resposta.status_code}"
print("✅ Bloqueado corretamente apos expiracao.\n")

# ---------------------------------------------------------------------------
# 7. Vara sempre pode ler, independente de permissao (esperado: 200)
# ---------------------------------------------------------------------------

print("7) Vara consultando o proprio documento (esperado: 200, sempre tem acesso)...")
resposta = requests.get(f"{BASE_URL}/documentos/{doc_id}", headers=cabecalho(token_admin))
print(f"   status={resposta.status_code}")
assert resposta.status_code == 200
print("✅ Vara acessa sem precisar de permissao explicita.\n")

print("=" * 60)
print("TODOS OS TESTES DE PERMISSAO DE LEITURA PASSARAM ✅")
print("=" * 60)