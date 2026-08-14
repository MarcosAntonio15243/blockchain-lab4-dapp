# teste_auditoria.py — trilha de consultas por QR Code
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
aerea = Account.create()
policia = Account.create()

falhas = []
total = 0


def checar(descricao, obtido, esperado):
    global total
    total += 1
    ok = obtido in esperado if isinstance(esperado, tuple) else obtido == esperado
    print(f"   [{'OK  ' if ok else 'FALHA'}] {descricao} — esperado {esperado}, obtido {obtido}")
    if not ok:
        falhas.append(descricao)


def logar(conta):
    r = requests.post(f"{BASE_URL}/auth/nonce", json={"endereco": conta.address}, timeout=10)
    r.raise_for_status()
    a = Account.sign_message(encode_defunct(text=r.json()["mensagem"]), private_key=conta.key)
    r = requests.post(f"{BASE_URL}/auth/verificar",
                      json={"endereco": conta.address, "assinatura": a.signature.hex()}, timeout=10)
    r.raise_for_status()
    return r.json()["token"]


def cab(t):
    return {"Authorization": f"Bearer {t}"}


PDF = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>"
HASH_PDF = "0x" + hashlib.sha256(PDF).hexdigest()

# ----------------------------------------------------------------------
print("PREPARANDO")
token_admin = logar(admin)

for conta, perfil, nome in [
    (aerea, 3, "Companhia Aérea Exemplo - Filial Recife"),
    (policia, 2, "Polícia Federal - Delegacia de Campina Grande"),
]:
    r = requests.post(f"{BASE_URL}/acessos/definir-perfil",
                      json={"conta": conta.address, "perfil": perfil, "nome": nome},
                      headers=cab(token_admin), timeout=15)
    if r.status_code >= 300:
        print(f"   !! erro ao definir perfil ({r.status_code}): {r.text}")
        sys.exit(1)
    print(f"   {nome} → {conta.address}")

r = requests.post(f"{BASE_URL}/documentos",
                  json={"hashDocumento": HASH_PDF,
                        "tipoDocumento": "Alvará de Autorização de Viagem",
                        "orgaoEmissor": "2ª Vara da Infância e Juventude de Campina Grande",
                        "autoridadeSignataria": "Dra. Maria Exemplo, Juíza de Direito",
                        "validoAte": "2026-12-31"},
                  headers=cab(token_admin), timeout=20)
r.raise_for_status()
doc_id = r.json().get("docId") or r.json().get("doc_id")

requests.post(f"{BASE_URL}/documentos/{doc_id}/dados-sensiveis",
              json={"docId": doc_id, "categoria": "alvara_viagem",
                    "nomeCrianca": "Marina Souza Exemplo",
                    "nomeAcompanhante": "Carlos Souza Exemplo (pai)",
                    "destinoViagem": "Lisboa/Portugal"},
              headers=cab(token_admin), timeout=10).raise_for_status()
print(f"   doc_id: {doc_id}")

# Grant só para a companhia aérea
requests.post(f"{BASE_URL}/permissoes",
              json={"docId": doc_id, "endereco": aerea.address},
              headers=cab(token_admin), timeout=10)
print("   grant: aérea SIM, polícia NÃO\n")

token_aerea = logar(aerea)
token_policia = logar(policia)

# ----------------------------------------------------------------------
print("GERANDO CONSULTAS")
requests.get(f"{BASE_URL}/validacao/{doc_id}", timeout=10)                              # anônima
requests.get(f"{BASE_URL}/validacao/{doc_id}", timeout=10)                              # anônima
requests.get(f"{BASE_URL}/validacao/{doc_id}", headers=cab(token_aerea), timeout=10)    # ampliada
requests.get(f"{BASE_URL}/validacao/{doc_id}", headers=cab(token_policia), timeout=10)  # básica
requests.get(f"{BASE_URL}/validacao/{doc_id}", headers=cab(token_admin), timeout=10)    # ampliada
print("   5 consultas: 2 anônimas, 1 aérea (com grant), 1 PF (sem grant), 1 Vara\n")

# ----------------------------------------------------------------------
print("TRILHA")
r = requests.get(f"{BASE_URL}/documentos/{doc_id}/consultas",
                 headers=cab(token_admin), timeout=10)
checar("Vara lê a trilha", r.status_code, 200)
if r.status_code != 200:
    print(f"   corpo: {r.text}")
    sys.exit(1)

trilha = r.json()
checar("5 consultas registradas", len(trilha), 5)

for c in trilha:
    quem = c.get("nomeInstituicao") or c.get("endereco") or "ANÔNIMO"
    nivel = "ampliado" if c.get("acessoAmpliado") else "básico"
    print(f"      {c.get('consultadoEm')}  {nivel:9} {c.get('perfil') or '-':16} {quem}")

anonimas = [c for c in trilha if c.get("endereco") is None]
checar("2 consultas anônimas", len(anonimas), 2)
checar("anônima sem instituição", anonimas[0].get("nomeInstituicao"), None)

ampliadas = [c for c in trilha if c.get("acessoAmpliado")]
checar("2 consultas ampliadas (aérea + Vara)", len(ampliadas), 2)

com_nome = [c for c in trilha if c.get("nomeInstituicao")]
checar("instituições identificadas pelo nome", len(com_nome) >= 2, True)

nomes = {c.get("nomeInstituicao") for c in trilha if c.get("nomeInstituicao")}
checar("nome da aérea na trilha",
       any("Companhia Aérea" in (n or "") for n in nomes), True)
checar("nome da PF na trilha",
       any("Polícia Federal" in (n or "") for n in nomes), True)

pf = [c for c in trilha
      if "Polícia Federal" in (c.get("nomeInstituicao") or "")]
checar("PF consultou mas NÃO teve acesso ampliado",
       pf[0].get("acessoAmpliado") if pf else None, False)

# ----------------------------------------------------------------------
print("\nFILTROS")
r = requests.get(f"{BASE_URL}/documentos/{doc_id}/consultas?apenas_ampliadas=true",
                 headers=cab(token_admin), timeout=10).json()
checar("filtro apenas_ampliadas=true", len(r), 2)

r = requests.get(f"{BASE_URL}/documentos/{doc_id}/consultas?apenas_ampliadas=false",
                 headers=cab(token_admin), timeout=10).json()
checar("filtro apenas_ampliadas=false", len(r), 3)

r = requests.get(f"{BASE_URL}/documentos/{doc_id}/consultas?perfil=COMPANHIA_AEREA",
                 headers=cab(token_admin), timeout=10).json()
checar("filtro por perfil COMPANHIA_AEREA", len(r), 1)

# ----------------------------------------------------------------------
print("\nAUTORIZAÇÃO DA TRILHA")
checar("externo não lê a trilha",
       requests.get(f"{BASE_URL}/documentos/{doc_id}/consultas",
                    headers=cab(token_aerea), timeout=10).status_code, 403)
checar("anônimo não lê a trilha",
       requests.get(f"{BASE_URL}/documentos/{doc_id}/consultas", timeout=10).status_code,
       (401, 403))

# ----------------------------------------------------------------------
print("\nAUDITORIA NÃO PODE DERRUBAR A VALIDAÇÃO")
antes = len(requests.get(f"{BASE_URL}/documentos/{doc_id}/consultas",
                         headers=cab(token_admin), timeout=10).json())
r = requests.get(f"{BASE_URL}/validacao/{doc_id}", timeout=10)
checar("validação continua respondendo 200", r.status_code, 200)
depois = len(requests.get(f"{BASE_URL}/documentos/{doc_id}/consultas",
                          headers=cab(token_admin), timeout=10).json())
checar("e a consulta foi registrada", depois, antes + 1)

# ----------------------------------------------------------------------
print("\n" + "=" * 70)
if falhas:
    print(f"{total - len(falhas)}/{total} OK — {len(falhas)} FALHA(S):")
    for f in falhas:
        print(f"   - {f}")
else:
    print(f"{total}/{total} OK — trilha de consultas funcionando.")
print("=" * 70)