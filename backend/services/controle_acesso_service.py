import json
from web3 import Web3
from sqlalchemy.orm import Session
from backend.models.instituicao import Instituicao
from backend.schemas.controle_acesso import PerfilEnum

from backend.schemas.registrar_documento import PerfilOnChain

class ControleAcessoService:
    def __init__(self, w3: Web3, contract_address: str, abi: list, private_key: str, db: Session):
        self.w3 = w3
        self.db = db
        self.chave_privada = private_key
        self.conta_admin = self.w3.eth.account.from_key(private_key).address
        self.contrato = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=abi
        )


    def definir_perfil(self, conta_alvo: str, perfil_enum: int, nome: str) -> str:
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

        self.db.add(instituicao)
        self.db.commit()
        self.db.refresh(instituicao)

        existente = self.db.query(Instituicao).filter(Instituicao.endereco == conta_alvo).first()
        if existente is not None:
            raise ValueError("ja existe um registro de instituicao para este endereco")

        instituicao = Instituicao(
            endereco=conta_alvo,
            nome=nome,
            cadastrado_por=cadastrado_por.lower(),
        )

        return comprovante.transactionHash.hex()

    # Consulta o nome da instituição e quem a registrou
    def consultar_instituicao(self, endereco: str) -> Instituicao | None:
        return self.db.query(Instituicao).filter(Instituicao.endereco == endereco.lower()).first()

    def consultar_perfil(self, conta: str) -> PerfilOnChain:
        perfil_bruto = self.contrato.functions.perfilDe(
            self.w3.to_checksum_address(conta)
        ).call()
        return PerfilOnChain(perfil_bruto)
