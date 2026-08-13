// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

// Importa o contrato de controle de perfis para que este contrato possa referencia-lo.
import "./ControleAcesso.sol";

// Contrato responsavel por registrar e consultar documentos sigilosos na blockchain.
contract RegistroDocumentos {
    enum StatusDocumento {
        Valido,
        Expirado,
        Revogado,
        Substituido
    }

    // Estrutura que representa os dados do documento guardados on-chain.
    struct Documento {
        bytes32 hashDocumento; // Hash do PDFo.
        string tipoDocumento; // Ex: alvara de viagem, termo de guarda, etc.
        string orgaoEmissor;
        string autoridadeSignataria; // Nome/cargo da autoridade que assinou o documento.
        bytes32 hashAssinatura; // Hash da assinatura eletronica.
        uint256 emitidoEm;
        uint256 validoAte; // Data limite de validade; zero significa sem validade definida.
        StatusDocumento status;
        bytes32 substituidoPor; // docId do novo documento, caso este tenha sido substituido.
        uint256 statusAtualizadoEm; // Data e hora da ultima revogacao/substituicao registrada.
        bool existe;
    }

    // Endereco da conta que representa a Vara e pode gerenciar documentos.
    address public vara;

    // Referencia ao contrato que gerencia perfis de acesso.
    ControleAcesso public controleAcesso;

    // Tabela que liga um docId aos dados registrados do documento.
    mapping(bytes32 => Documento) private documentos;

    event DocumentoRegistrado(
        bytes32 indexed docId,
        bytes32 indexed hashDocumento,
        string tipoDocumento,
        string orgaoEmissor,
        uint256 validoAte
    );

    event DocumentoRevogado(bytes32 indexed docId);

    event DocumentoSubstituido(bytes32 indexed docId, bytes32 indexed novoDocId);

    // Modificador que restringe uma funcao apenas a conta da Vara.
    modifier somenteVara() {
        // Interrompe a execucao se quem chamou a funcao nao for a Vara.
        require(msg.sender == vara, "somente vara");

        // Continua a execucao da funcao protegida pelo modificador.
        _;
    }

    constructor(address enderecoControleAcesso) {
        // Quem implanta este contrato vira a conta administradora da Vara.
        vara = msg.sender;

        controleAcesso = ControleAcesso(enderecoControleAcesso);
    }

    function registrarDocumento(
        bytes32 docId,
        bytes32 hashDocumento,
        string calldata tipoDocumento,
        string calldata orgaoEmissor,
        string calldata autoridadeSignataria,
        bytes32 hashAssinatura,
        uint256 validoAte
    ) external somenteVara {
        require(!documentos[docId].existe, "documento ja registrado");

        documentos[docId] = Documento({
            hashDocumento: hashDocumento,
            tipoDocumento: tipoDocumento,
            orgaoEmissor: orgaoEmissor,
            autoridadeSignataria: autoridadeSignataria,
            hashAssinatura: hashAssinatura,
            emitidoEm: block.timestamp,
            validoAte: validoAte,
            status: StatusDocumento.Valido,
            substituidoPor: bytes32(0),
            statusAtualizadoEm: block.timestamp,
            existe: true
        });

        emit DocumentoRegistrado(docId, hashDocumento, tipoDocumento, orgaoEmissor, validoAte);
    }

    function documentoExiste(bytes32 docId) external view returns (bool) {
        return documentos[docId].existe;
    }

    // Retorna os metadados e o status atual de um documento.
    function verificarDocumento(bytes32 docId)
        external
        view
        returns (
            bool existe,
            bytes32 hashDocumento,
            string memory tipoDocumento,
            string memory orgaoEmissor,
            string memory autoridadeSignataria,
            bytes32 hashAssinatura,
            uint256 emitidoEm,
            uint256 validoAte,
            StatusDocumento status,
            bytes32 substituidoPor,
            uint256 statusAtualizadoEm
        )
    {
        Documento memory documento = documentos[docId];

        return (
            documento.existe,
            documento.hashDocumento,
            documento.tipoDocumento,
            documento.orgaoEmissor,
            documento.autoridadeSignataria,
            documento.hashAssinatura,
            documento.emitidoEm,
            documento.validoAte,
            statusAtualInterno(documento),
            documento.substituidoPor,
            documento.statusAtualizadoEm
        );
    }

    function revogarDocumento(bytes32 docId) external somenteVara {
        require(documentos[docId].existe, "documento inexistente");

        documentos[docId].status = StatusDocumento.Revogado;
        documentos[docId].statusAtualizadoEm = block.timestamp;

        emit DocumentoRevogado(docId);
    }

    function substituirDocumento(bytes32 docId, bytes32 novoDocId) external somenteVara {
        require(documentos[docId].existe, "documento inexistente");
        require(documentos[novoDocId].existe, "novo documento inexistente");

        documentos[docId].status = StatusDocumento.Substituido;
        documentos[docId].substituidoPor = novoDocId;
        documentos[docId].statusAtualizadoEm = block.timestamp;

        emit DocumentoSubstituido(docId, novoDocId);
    }

    function statusAtual(bytes32 docId) external view returns (StatusDocumento) {
        require(documentos[docId].existe, "documento inexistente");

        // Usa a funcao interna para considerar expiracao automatica.
        return statusAtualInterno(documentos[docId]);
    }

    // Calcula o status atual considerando a data de validade.
    function statusAtualInterno(Documento memory documento) private view returns (StatusDocumento) {
        // Se o documento esta valido, possui validade e a validade passou, ele e tratado como expirado.
        if (
            documento.status == StatusDocumento.Valido &&
            documento.validoAte != 0 &&
            block.timestamp > documento.validoAte
        ) {
            return StatusDocumento.Expirado;
        }

        // Caso contrario, retorna o status que esta salvo.
        return documento.status;
    }
}
