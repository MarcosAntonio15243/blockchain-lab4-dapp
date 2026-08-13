# teste_negativo.py — testa o que DEVE ser bloqueado
import os
import sys
import hashlib
import requests
from eth_account import Account
from eth_account.messages import encode_defunct

BASE_URL = "http://localhost:8000/api/v1"

CHAVE_ADMIN = os.environ.get("CHAVE_PRIVADA_ADMIN")
if not CHAVE_ADMIN:
    print("Defina CHAVE_PRIVADA_ADMIN antes de rodar.")
    sys.exit(1)

admin = Account.from_key(CHAVE_ADMIN)
externo = Account.create()      # vira CompanhiaAerea
estranho = Account.create()     # fica sem perfil nenhum

falhas = []
total = 0


def checar(descricao, obtido, esperado):
    """Compara e registra. esperado pode ser valor unico ou tupla de aceitos."""
    global total
    total += 1
    ok = obtido in esperado if isinstance(esperado, tuple) else obtido == esperado
    marca = "OK  " if ok else "FALHA"
    print(f"   [{marca}] {descricao} — esperado {esperado}, obtido {obtido}")
    if not ok:
        falhas.append(descricao)


def logar(conta) -> str:
    r = requests.post(f"{BASE_URL}/auth/nonce", json={"endereco": conta.address}, timeout=10)
    r.raise_for_status()
    mensagem = r.json()["mensagem"]
    assinatura = Account.sign_message(encode_defunct(text=mensagem), private_key=conta.key)
    r = requests.post(
        f"{BASE_URL}/auth/verificar",
        json={"endereco": conta.address, "assinatura": assinatura.signature.hex()},
        timeout=10,
    )
    r.raise_for_status()
    return r.json()["token"]


def cab(token):
    return {"Authorization": f"Bearer {token}"}


def definir_perfil(token_quem, endereco, perfil):
    return requests.post(
        f"{BASE_URL}/acessos/definir-perfil",
        json={"conta": endereco, "perfil": perfil},
        headers=cab(token_quem),
        timeout=15,
    )


def criar_documento(token_admin, hash_doc, tipo, nome, categoria, extras):
    r = requests.post(
        f"{BASE_URL}/documentos",
        json={
            "hashDocumento": hash_doc,
            "tipoDocumento": tipo,
            "orgaoEmissor": "2ª Vara da Infância e Juventude de Campina Grande",
            "autoridadeSignataria": "Dra. Maria Exemplo, Juíza de Direito",
        },
        headers=cab(token_admin),
        timeout=15,
    )
    r.raise_for_status()
    doc_id = r.json().get("docId") or r.json().get("doc_id")

    corpo = {"docId": doc_id, "categoria": categoria, "nomeCrianca": nome}
    corpo.update(extras)
    r = requests.post(
        f"{BASE_URL}/documentos/{doc_id}/dados-sensiveis",
        json=corpo, headers=cab(token_admin), timeout=10,
    )
    r.raise_for_status()
    return doc_id


# ----------------------------------------------------------------------
print("PREPARANDO CENÁRIO")
token_admin = logar(admin)
print(f"   Vara:     {admin.address}")
print(f"   Externo:  {externo.address}")
print(f"   Estranho: {estranho.address}")

r = definir_perfil(token_admin, externo.address, 3)  # 3 = CompanhiaAerea
if r.status_code >= 300:
    print(f"\n   !! Falha ao definir perfil ({r.status_code}): {r.text}")
    sys.exit(1)

PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>"
HASH_PDF = "0x" + hashlib.sha256(PDF).hexdigest()

doc_a = criar_documento(token_admin, HASH_PDF, "Alvará de Autorização de Viagem",
                        "Marina Souza Exemplo", "alvara_viagem",
                        {"nomeAcompanhante": "Carlos Souza Exemplo (pai)",
                         "destinoViagem": "Lisboa/Portugal"})
doc_b = criar_documento(token_admin, HASH_PDF, "Termo de Guarda",
                        "Pedro Lima Exemplo", "termo_guarda",
                        {"nomeGuardiao": "Ana Lima Exemplo (avó)"})
print(f"   DOC_A: {doc_a}")
print(f"   DOC_B: {doc_b}")

requests.post(f"{BASE_URL}/documentos/{doc_a}/arquivo",
              files={"arquivo": ("alvara.pdf", PDF, "application/pdf")},
              headers=cab(token_admin), timeout=10)
requests.post(f"{BASE_URL}/documentos/{doc_b}/arquivo",
              files={"arquivo": ("termo.pdf", PDF, "application/pdf")},
              headers=cab(token_admin), timeout=10)

# Grant SOMENTE para o DOC_A
r = requests.post(f"{BASE_URL}/permissoes",
                  json={"docId": doc_a, "endereco": externo.address},
                  headers=cab(token_admin), timeout=10)
if r.status_code >= 300:
    print(f"\n   !! Falha ao conceder permissão ({r.status_code}): {r.text}")
    sys.exit(1)
print("   Grant concedido: externo -> DOC_A apenas\n")

token_externo = logar(externo)
token_estranho = logar(estranho)

# ----------------------------------------------------------------------
print("BLOCO 1 — AUTENTICAÇÃO")
checar("rota protegida sem header",
       requests.get(f"{BASE_URL}/documentos", timeout=10).status_code, (401, 403))
checar("token corrompido",
       requests.get(f"{BASE_URL}/documentos",
                    headers={"Authorization": "Bearer abc.def.ghi"}, timeout=10).status_code, 401)
checar("header sem 'Bearer'",
       requests.get(f"{BASE_URL}/documentos",
                    headers={"Authorization": token_admin}, timeout=10).status_code, (401, 403))

r = requests.post(f"{BASE_URL}/auth/nonce", json={"endereco": estranho.address}, timeout=10)
msg = r.json()["mensagem"]
assin = Account.sign_message(encode_defunct(text=msg), private_key=estranho.key)
requests.post(f"{BASE_URL}/auth/verificar",
              json={"endereco": estranho.address, "assinatura": assin.signature.hex()}, timeout=10)
r2 = requests.post(f"{BASE_URL}/auth/verificar",
                   json={"endereco": estranho.address, "assinatura": assin.signature.hex()}, timeout=10)
checar("nonce reutilizado", r2.status_code, 400)

r = requests.post(f"{BASE_URL}/auth/nonce", json={"endereco": admin.address}, timeout=10)
msg = r.json()["mensagem"]
assin_errada = Account.sign_message(encode_defunct(text=msg), private_key=estranho.key)
r = requests.post(f"{BASE_URL}/auth/verificar",
                  json={"endereco": admin.address, "assinatura": assin_errada.signature.hex()},
                  timeout=10)
checar("assinatura de outra carteira", r.json().get("autenticado"), False)

# ----------------------------------------------------------------------
print("\nBLOCO 2 — AUTORIZAÇÃO POR PERFIL")
checar("externo lista documentos",
       requests.get(f"{BASE_URL}/documentos", headers=cab(token_externo), timeout=10).status_code, 403)
checar("externo registra documento",
       requests.post(f"{BASE_URL}/documentos",
                     json={"hashDocumento": HASH_PDF, "tipoDocumento": "x",
                           "orgaoEmissor": "x", "autoridadeSignataria": "x"},
                     headers=cab(token_externo), timeout=15).status_code, 403)
checar("externo cadastra dados sensíveis",
       requests.post(f"{BASE_URL}/documentos/{doc_a}/dados-sensiveis",
                     json={"docId": doc_a, "categoria": "alvara_viagem", "nomeCrianca": "X"},
                     headers=cab(token_externo), timeout=10).status_code, 403)
checar("externo concede permissão",
       requests.post(f"{BASE_URL}/permissoes",
                     json={"docId": doc_b, "endereco": externo.address},
                     headers=cab(token_externo), timeout=10).status_code, 403)
checar("externo revoga documento",
       requests.post(f"{BASE_URL}/documentos/{doc_a}/revogar",
                     headers=cab(token_externo), timeout=15).status_code, 403)
checar("externo se autopromove a Vara",
       definir_perfil(token_externo, externo.address, 1).status_code, 403)
checar("sem perfil lista documentos",
       requests.get(f"{BASE_URL}/documentos", headers=cab(token_estranho), timeout=10).status_code, 403)
checar("sem perfil define perfil",
       definir_perfil(token_estranho, estranho.address, 1).status_code, 403)

# ----------------------------------------------------------------------
print("\nBLOCO 3 — GRANT POR DOCUMENTO (o coração do projeto)")
a = requests.get(f"{BASE_URL}/validacao/{doc_a}", headers=cab(token_externo), timeout=10).json()
checar("externo COM grant vê DOC_A ampliado", a.get("acesso_ampliado"), True)
checar("externo COM grant vê o nome", a.get("nome_crianca_adolescente"), "Marina Souza Exemplo")

b = requests.get(f"{BASE_URL}/validacao/{doc_b}", headers=cab(token_externo), timeout=10).json()
checar("externo SEM grant NÃO vê DOC_B ampliado", b.get("acesso_ampliado"), False)
checar("externo SEM grant NÃO vê o nome", b.get("nome_crianca_adolescente"), None)

checar("externo sem grant lê metadados de DOC_B",
       requests.get(f"{BASE_URL}/documentos/{doc_b}", headers=cab(token_externo), timeout=10).status_code, 403)
checar("externo sem grant baixa PDF de DOC_B",
       requests.get(f"{BASE_URL}/documentos/{doc_b}/arquivo", headers=cab(token_externo), timeout=10).status_code, 403)

anon = requests.get(f"{BASE_URL}/validacao/{doc_a}", timeout=10).json()
checar("anônimo NÃO vê ampliado", anon.get("acesso_ampliado"), False)
checar("anônimo NÃO vê o nome", anon.get("nome_crianca_adolescente"), None)
checar("anônimo VÊ o status", anon.get("situacao"), "Valido")

vara = requests.get(f"{BASE_URL}/validacao/{doc_b}", headers=cab(token_admin), timeout=10).json()
checar("Vara vê qualquer documento", vara.get("acesso_ampliado"), True)

# ----------------------------------------------------------------------
print("\nBLOCO 4 — INTEGRIDADE E STATUS")
r = requests.post(f"{BASE_URL}/validacao/{doc_a}/conferir-integridade",
                  files={"arquivo": ("ok.pdf", PDF, "application/pdf")}, timeout=10).json()
checar("PDF correto é íntegro", r.get("integro"), True)

r = requests.post(f"{BASE_URL}/validacao/{doc_a}/conferir-integridade",
                  files={"arquivo": ("mau.pdf", b"%PDF-1.4 adulterado", "application/pdf")},
                  timeout=10).json()
checar("PDF adulterado é recusado", r.get("integro"), False)

checar("doc_id inexistente",
       requests.get(f"{BASE_URL}/validacao/0x" + "ff" * 32, timeout=10).status_code, 404)

requests.post(f"{BASE_URL}/documentos/{doc_a}/revogar", headers=cab(token_admin), timeout=15)
rev = requests.get(f"{BASE_URL}/validacao/{doc_a}", timeout=10).json()
checar("documento revogado muda de status", rev.get("situacao"), "Revogado")
checar("flag de não-revogado fica falsa", rev.get("nao_revogado_ou_substituido"), False)

# ----------------------------------------------------------------------
print("\n" + "=" * 70)
if falhas:
    print(f"{total - len(falhas)}/{total} OK — {len(falhas)} FALHA(S):")
    for f in falhas:
        print(f"   - {f}")
else:
    print(f"{total}/{total} OK — tudo que deve ser bloqueado está bloqueado.")
print("=" * 70)