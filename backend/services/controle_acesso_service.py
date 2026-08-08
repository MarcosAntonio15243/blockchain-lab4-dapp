import json
from web3 import Web3
from backend.schemas.controle_acesso import PerfilEnum

class ControleAcessoService:
    def __init__(self, w3: Web3, contract_address: str, abi: list, private_key: str):
        self.w3 = w3
        self.chave_privada = private_key
        self.conta_admin = self.w3.eth.account.from_key(private_key).address
        self.contrato = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=abi
        )

    def definir_perfil(self, conta_alvo: str, perfil_enum: int) -> str:
        conta_checksum = Web3.to_checksum_address(conta_alvo)
        nonce = self.w3.eth.get_transaction_count(self.conta_admin)

        transacao = self.contrato.functions.definirPerfil(
            conta_checksum, 
            int(perfil_enum)
        ).build_transaction({
            'from': self.conta_admin,
            'nonce': nonce,
            'gas': 100000,
            'gasPrice': self.w3.eth.gas_price
        })

        transacao_assinada = self.w3.eth.account.sign_transaction(transacao, self.chave_privada)
        transacao_hash = self.w3.eth.send_raw_transaction(transacao_assinada.raw_transaction)
        comprovante = self.w3.eth.wait_for_transaction_receipt(transacao_hash)
        return comprovante.transactionHash.hex()

    def consultar_perfil(self, conta: str) -> PerfilOnChain:
        perfil_bruto = self.contract.functions.perfilDe(
            self.w3.to_checksum_address(conta)
        ).call()
        return PerfilOnChain(perfil_bruto)

