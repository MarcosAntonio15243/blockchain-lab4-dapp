"""
Atribui um perfil institucional a uma conta na blockchain, sem precisar
montar chamadas HTTP manuais nem ficar catando token de sessão no navegador.

Uso:
    venv/bin/python3 atribuir_perfil.py <endereco_da_conta> <perfil>

<perfil> pode ser: Vara, PoliciaFederal, CompanhiaAerea, ConselhoTutelar

Exemplo:
    venv/bin/python3 atribuir_perfil.py 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 PoliciaFederal

Faz login como a conta administradora (a mesma que implanta os contratos,
CHAVE_PRIVADA_ADMIN em backend/.env, que já nasce com perfil Vara) e chama
POST /acessos/definir-perfil autenticado com o token dela.

Requer o backend rodando em http://127.0.0.1:8000 (ajuste BASE abaixo se for
diferente) e os contratos já implantados (ver deploy-contratos.sh).
"""

import sys

import requests
from eth_account import Account
from eth_account.messages import encode_defunct

BASE = "http://127.0.0.1:8000/api/v1"
CHAVE_PRIVADA_ADMIN = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

PERFIL_POR_NOME = {
    "nenhum": 0,
    "vara": 1,
    "policiafederal": 2,
    "companhiaaerea": 3,
    "conselhotutelar": 4,
}


def logar_como_admin() -> str:
    conta = Account.from_key(CHAVE_PRIVADA_ADMIN)
    endereco = conta.address

    resposta = requests.post(f"{BASE}/auth/nonce", json={"endereco": endereco})
    resposta.raise_for_status()
    mensagem = resposta.json()["mensagem"]

    assinatura = Account.sign_message(
        encode_defunct(text=mensagem), private_key=CHAVE_PRIVADA_ADMIN
    ).signature.hex()
    if not assinatura.startswith("0x"):
        assinatura = "0x" + assinatura

    resposta = requests.post(
        f"{BASE}/auth/verificar", json={"endereco": endereco, "assinatura": assinatura}
    )
    resposta.raise_for_status()
    dados = resposta.json()
    if not dados.get("autenticado"):
        raise SystemExit("Falha ao autenticar como administrador — assinatura rejeitada.")
    return dados["token"]


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(1)

    endereco_alvo = sys.argv[1]
    nome_perfil = sys.argv[2]
    perfil_numero = PERFIL_POR_NOME.get(nome_perfil.lower())
    if perfil_numero is None:
        print(f"Perfil desconhecido: {nome_perfil!r}. Use um de: {list(PERFIL_POR_NOME)}")
        raise SystemExit(1)

    token = logar_como_admin()

    resposta = requests.post(
        f"{BASE}/acessos/definir-perfil",
        headers={"Authorization": f"Bearer {token}"},
        json={"conta": endereco_alvo, "perfil": perfil_numero},
    )

    if resposta.status_code != 200:
        print(f"Erro ({resposta.status_code}): {resposta.text}")
        raise SystemExit(1)

    print(f"OK — {endereco_alvo} agora tem perfil {nome_perfil} ({perfil_numero}).")
    print(resposta.json())


if __name__ == "__main__":
    main()
