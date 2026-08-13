#!/bin/bash
set -e

ENV_FILE=backend/.env

echo "[1/4] Compilando contratos Solidity..."
forge build

echo "[2/4] Copiando ABI compilada para o Backend..."
mkdir -p backend/abi
cp out/ControleAcesso.sol/ControleAcesso.json backend/abi/ControleAcesso.json
cp out/RegistroDocumentos.sol/RegistroDocumentos.json backend/abi/RegistroDocumentos.json

echo "[3/4] Realizando Deploy no nó Anvil local..."
CHAVE_ADMIN=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
RPC=http://127.0.0.1:8545

CONTROLE_ACESSO_OUTPUT=$(forge create contracts/ControleAcesso.sol:ControleAcesso \
  --rpc-url "$RPC" --private-key "$CHAVE_ADMIN" --broadcast)
CONTROLE_ACESSO_ADDRESS=$(echo "$CONTROLE_ACESSO_OUTPUT" | grep "Deployed to:" | awk '{print $3}' | tail -n 1)

REGISTRO_DOCUMENTOS_OUTPUT=$(forge create contracts/RegistroDocumentos.sol:RegistroDocumentos \
  --rpc-url "$RPC" --private-key "$CHAVE_ADMIN" --broadcast \
  --constructor-args "$CONTROLE_ACESSO_ADDRESS")
REGISTRO_DOCUMENTOS_ADDRESS=$(echo "$REGISTRO_DOCUMENTOS_OUTPUT" | grep "Deployed to:" | awk '{print $3}' | tail -n 1)

echo "[4/4] Atualizando .env (preservando os demais valores)..."

# Cria o .env na primeira execução, com um JWT_SECRET_KEY novo.
if [ ! -f "$ENV_FILE" ]; then
  {
    echo "BLOCKCHAIN_RPC_URL=$RPC"
    echo "CHAVE_PRIVADA_ADMIN=$CHAVE_ADMIN"
    echo "JWT_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
  } > "$ENV_FILE"
fi

# Substitui a chave se já existir; acrescenta se não existir.
atualizar_env() {
  local chave=$1 valor=$2
  if grep -q "^${chave}=" "$ENV_FILE"; then
    sed -i "s|^${chave}=.*|${chave}=${valor}|" "$ENV_FILE"
  else
    echo "${chave}=${valor}" >> "$ENV_FILE"
  fi
}

atualizar_env ENDERECO_CONTROLE_ACESSO "$CONTROLE_ACESSO_ADDRESS"
atualizar_env ENDERECO_REGISTRO_DOCUMENTOS "$REGISTRO_DOCUMENTOS_ADDRESS"

echo ""
echo "==============================================================="
echo "✅ Contratos implantados com sucesso!"
echo "   ENDERECO_CONTROLE_ACESSO=$CONTROLE_ACESSO_ADDRESS"
echo "   ENDERECO_REGISTRO_DOCUMENTOS=$REGISTRO_DOCUMENTOS_ADDRESS"
echo "==============================================================="