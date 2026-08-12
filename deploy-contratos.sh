#!/bin/bash

set -e

echo "[1/3] Compilando contratos Solidity..."
forge build

echo "[2/3] Copiando ABI compilada para o Backend..."
mkdir -p backend/abi
cp out/ControleAcesso.sol/ControleAcesso.json backend/abi/ControleAcesso.json
cp out/RegistroDocumentos.sol/RegistroDocumentos.json backend/abi/RegistroDocumentos.json


echo "[3/3] Realizando Deploy no nó Anvil local..."
CONTROLE_ACESSO_OUTPUT=$(forge create contracts/ControleAcesso.sol:ControleAcesso \
  --rpc-url http://127.0.0.1:8545 \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
  --broadcast)

# Extrai o endereço "Deployed to:" retornado pelo Forge.
CONTROLE_ACESSO_ADDRESS=$(echo "$CONTROLE_ACESSO_OUTPUT" | grep "Deployed to:" | awk '{print $3}' | tail -n 1)

REGISTRO_DOCUMENTOS_OUTPUT=$(forge create contracts/RegistroDocumentos.sol:RegistroDocumentos \
  --rpc-url http://127.0.0.1:8545 \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
  --broadcast \
  --constructor-args "$CONTROLE_ACESSO_ADDRESS")

REGISTRO_DOCUMENTOS_ADDRESS=$(echo "$REGISTRO_DOCUMENTOS_OUTPUT" | grep "Deployed to:" | awk '{print $3}' | tail -n 1)

printf '%s\n' \
  "ENDERECO_CONTROLE_ACESSO=$CONTROLE_ACESSO_ADDRESS" \
  "ENDERECO_REGISTRO_DOCUMENTOS=$REGISTRO_DOCUMENTOS_ADDRESS" \
  "BLOCKCHAIN_RPC_URL=http://127.0.0.1:8545" \
  "CHAVE_PRIVADA_ADMIN=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80" \
  > backend/.env

echo ""
echo "==============================================================="
echo "✅ Contrato implantado com sucesso!"
echo "📍 Endereços gravados automaticamente no arquivo .env:"
echo "   ENDERECO_CONTROLE_ACESSO=$CONTROLE_ACESSO_ADDRESS"
echo "   ENDERECO_REGISTRO_DOCUMENTOS=$REGISTRO_DOCUMENTOS_ADDRESS"
echo "==============================================================="
