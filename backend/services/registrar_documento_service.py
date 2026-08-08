from datetime import datetime, timezone
from uuid import uuid4

from web3 import Web3

from backend.schemas.registrar_documento import DocumentoInput, PerfilConsulente


STATUS = {0: "Valido", 1: "Expirado", 2: "Revogado", 3: "Substituido"}


class RegistrarDocumentoService:
    def __init__(self, w3: Web3, contract_address: str, abi: list, private_key: str):
        self.w3 = w3
        self.chave_privada = private_key
        self.conta_vara = self.w3.eth.account.from_key(private_key).address
        self.contrato = self.w3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=abi,
        )

    @staticmethod
    def _bytes32(valor: str) -> bytes:
        valor = valor if valor.startswith("0x") else f"0x{valor}"
        resultado = Web3.to_bytes(hexstr=valor)
        if len(resultado) != 32:
            raise ValueError("O valor deve conter 32 bytes.")
        return resultado

    def _enviar(self, funcao, gas: int = 1_000_000) -> str:
        transacao = funcao.build_transaction({
            "from": self.conta_vara,
            "nonce": self.w3.eth.get_transaction_count(self.conta_vara),
            "gas": gas,
            "gasPrice": self.w3.eth.gas_price,
        })
        assinada = self.w3.eth.account.sign_transaction(transacao, self.chave_privada)
        hash_transacao = self.w3.eth.send_raw_transaction(assinada.raw_transaction)
        comprovante = self.w3.eth.wait_for_transaction_receipt(hash_transacao)
        return comprovante.transactionHash.hex()

    def registrar(self, requisicao: DocumentoInput) -> dict:
        doc_id = Web3.to_hex(Web3.keccak(text=f"documento:{uuid4()}"))
        valido_ate = 0
        if requisicao.valido_ate:
            valido_ate = int(
                datetime.strptime(requisicao.valido_ate, "%Y-%m-%d")
                .replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)
                .timestamp()
            )

        hash_transacao = self._enviar(
            self.contrato.functions.registrarDocumento(
                self._bytes32(doc_id),
                self._bytes32(requisicao.hash_documento),
                requisicao.tipo_documento,
                requisicao.orgao_emissor,
                requisicao.autoridade_signataria,
                self._bytes32(requisicao.hash_assinatura or "0x" + "00" * 32),
                valido_ate,
            )
        )
        documento = self.consultar(doc_id)
        documento["hash_transacao"] = hash_transacao
        return documento

    def consultar(self, doc_id: str) -> dict:
        resposta = self.contrato.functions.verificarDocumento(
            self._bytes32(doc_id)
        ).call()
        if not resposta[0]:
            raise KeyError(doc_id)

        return {
            "doc_id": doc_id,
            "hash_documento": Web3.to_hex(resposta[1]),
            "tipo_documento": resposta[2],
            "orgao_emissor": resposta[3],
            "autoridade_signataria": None,
            "hash_assinatura": None,
            "emitido_em": datetime.fromtimestamp(
                int(resposta[4]), tz=timezone.utc
            ).isoformat(),
            "valido_ate": (
                datetime.fromtimestamp(int(resposta[5]), tz=timezone.utc)
                .date()
                .isoformat()
                if resposta[5]
                else None
            ),
            "status": STATUS[int(resposta[6])],
            "substituido_por": (
                None
                if bytes(resposta[7]) == bytes(32)
                else Web3.to_hex(resposta[7])
            ),
            "status_atualizado_em": None,
            "existe": True,
        }

    def listar(self) -> list[dict]:
        eventos = self.contrato.events.DocumentoRegistrado().get_logs(
            from_block=0,
            to_block="latest",
        )
        return [
            self.consultar(Web3.to_hex(evento["args"]["docId"]))
            for evento in eventos
        ]

    def revogar(self, doc_id: str) -> dict:
        self.consultar(doc_id)
        self._enviar(self.contrato.functions.revogarDocumento(self._bytes32(doc_id)))
        return self.consultar(doc_id)

    def substituir(self, doc_id: str, requisicao: DocumentoInput) -> dict:
        self.consultar(doc_id)
        novo_documento = self.registrar(requisicao)
        self._enviar(
            self.contrato.functions.substituirDocumento(
                self._bytes32(doc_id),
                self._bytes32(novo_documento["doc_id"]),
            )
        )
        return self.consultar(novo_documento["doc_id"])

    def validar(self, doc_id: str, perfil: PerfilConsulente) -> dict:
        documento = self.consultar(doc_id)
        campos = {
            PerfilConsulente.POLICIA_FEDERAL: ["tipo_documento", "orgao_emissor", "valido_ate"],
            PerfilConsulente.COMPANHIA_AEREA: ["tipo_documento", "valido_ate"],
            PerfilConsulente.CONSELHO_TUTELAR: ["tipo_documento", "orgao_emissor", "valido_ate"],
        }[perfil]
        return {
            "existe": True,
            "status": documento["status"],
            "campos_visiveis": {
                campo: documento[campo]
                for campo in campos
                if documento.get(campo)
            },
        }
