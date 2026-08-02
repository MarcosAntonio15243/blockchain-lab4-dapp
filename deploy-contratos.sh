#!/bin/bash

set -e

echo "[1/3] Compilando contratos Solidity..."
forge build

echo "[2/3] Copiando ABI compilada para o Backend..."
mkdir -p backend/abi
cp out/ControleAcesso.sol/ControleAcesso.json backend/abi/ControleAcesso.json

echo "[3/3] Realizando Deploy no nó Anvil local..."
DEPLOY_OUTPUT=$(forge create contracts/ControleAcesso.sol:ControleAcesso \
  --rpc-url http://127.0.0.1:8545 \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
  --broadcast)

# Extrai o endereço 'Deployed to:' retornado pelo Forge
CONTRACT_ADDRESS=$(echo "$DEPLOY_OUTPUT" | grep "Deployed to:" | awk '{print $3}')

echo "ENDERECO_CONTROLE_ACESSO=$CONTRACT_ADDRESS" > backend/.env

echo ""
echo "==============================================================="
echo "✅ Contrato implantado com sucesso!"
echo "📍 Endereço gravado automaticamente no arquivo .env:"
echo "   ENDERECO_CONTROLE_ACESSO=$CONTRACT_ADDRESS"
echo "==============================================================="