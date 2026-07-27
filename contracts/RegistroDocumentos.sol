// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

// Importa o contrato de controle de perfis para que este contrato possa referencia-lo.
import "./ControleAcesso.sol";

// Contrato responsavel por registrar e consultar documentos sigilosos na blockchain.
contract RegistroDocumentos {
    // Lista fechada dos status possiveis de um documento.
    enum StatusDocumento {
        Valido, // Documento ativo e dentro da validade.
        Expirado, // Documento passou da data de validade.
        Revogado, // Documento foi cancelado pela Vara.
        Substituido // Documento foi trocado por outro documento.
    }

    // Estrutura que representa os dados do documento guardados on-chain.
    struct Documento {
        bytes32 hashDocumento; // Hash do PDF, usado para provar integridade sem expor o arquivo.
        string tipoDocumento; // Exemplo: alvara de viagem ou termo de guarda.
        string orgaoEmissor; // Orgao judicial que emitiu o documento.
        uint256 emitidoEm; // Data e hora em que o registro foi feito na blockchain.
        uint256 validoAte; // Data limite de validade; zero significa sem validade definida.
        StatusDocumento status; // Status salvo do documento.
        bytes32 substituidoPor; // docId do novo documento, caso este tenha sido substituido.
        bool existe; // Indica se o documento ja foi registrado.
    }

    // Endereco da conta que representa a Vara e pode gerenciar documentos.
    address public vara;

    // Referencia ao contrato que gerencia perfis de acesso.
    ControleAcesso public controleAcesso;

    // Tabela que liga um docId aos dados registrados do documento.
    mapping(bytes32 => Documento) private documentos;

    // Evento emitido quando um novo documento e registrado.
    event DocumentoRegistrado(
        bytes32 indexed docId,
        bytes32 indexed hashDocumento,
        string tipoDocumento,
        string orgaoEmissor,
        uint256 validoAte
    );

    // Evento emitido quando um documento e revogado.
    event DocumentoRevogado(bytes32 indexed docId);

    // Evento emitido quando um documento e substituido por outro.
    event DocumentoSubstituido(bytes32 indexed docId, bytes32 indexed novoDocId);

    // Modificador que restringe uma funcao apenas a conta da Vara.
    modifier somenteVara() {
        // Interrompe a execucao se quem chamou a funcao nao for a Vara.
        require(msg.sender == vara, "somente vara");

        // Continua a execucao da funcao protegida pelo modificador.
        _;
    }

    // Executado uma unica vez quando o contrato e implantado.
    constructor(address enderecoControleAcesso) {
        // Quem implanta este contrato vira a conta administradora da Vara.
        vara = msg.sender;

        // Salva o endereco do contrato de controle de acesso.
        controleAcesso = ControleAcesso(enderecoControleAcesso);
    }

    // Registra um novo documento na blockchain.
    function registrarDocumento(
        bytes32 docId, // Identificador aleatorio do documento.
        bytes32 hashDocumento, // Hash do PDF assinado.
        string calldata tipoDocumento, // Tipo do documento.
        string calldata orgaoEmissor, // Orgao judicial emissor.
        uint256 validoAte // Data de validade em formato timestamp.
    ) external somenteVara {
        // Impede registrar duas vezes o mesmo docId.
        require(!documentos[docId].existe, "documento ja registrado");

        // Salva os dados minimos do documento na blockchain.
        documentos[docId] = Documento({
            hashDocumento: hashDocumento,
            tipoDocumento: tipoDocumento,
            orgaoEmissor: orgaoEmissor,
            emitidoEm: block.timestamp,
            validoAte: validoAte,
            status: StatusDocumento.Valido,
            substituidoPor: bytes32(0),
            existe: true
        });

        // Registra publicamente o evento de emissao do documento.
        emit DocumentoRegistrado(docId, hashDocumento, tipoDocumento, orgaoEmissor, validoAte);
    }

    // Verifica se um documento ja foi registrado.
    function documentoExiste(bytes32 docId) external view returns (bool) {
        // Retorna true se o docId existir no mapping.
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
            uint256 emitidoEm,
            uint256 validoAte,
            StatusDocumento status,
            bytes32 substituidoPor
        )
    {
        // Copia os dados do documento para memoria durante a consulta.
        Documento memory documento = documentos[docId];

        // Retorna os dados on-chain do documento.
        return (
            documento.existe,
            documento.hashDocumento,
            documento.tipoDocumento,
            documento.orgaoEmissor,
            documento.emitidoEm,
            documento.validoAte,
            statusAtualInterno(documento),
            documento.substituidoPor
        );
    }

    // Marca um documento como revogado.
    function revogarDocumento(bytes32 docId) external somenteVara {
        // So permite revogar documentos que ja existem.
        require(documentos[docId].existe, "documento inexistente");

        // Altera o status salvo para Revogado.
        documentos[docId].status = StatusDocumento.Revogado;

        // Registra publicamente o evento de revogacao.
        emit DocumentoRevogado(docId);
    }

    // Marca um documento como substituido por outro documento ja registrado.
    function substituirDocumento(bytes32 docId, bytes32 novoDocId) external somenteVara {
        // O documento antigo precisa existir.
        require(documentos[docId].existe, "documento inexistente");

        // O novo documento tambem precisa existir.
        require(documentos[novoDocId].existe, "novo documento inexistente");

        // Marca o documento antigo como substituido.
        documentos[docId].status = StatusDocumento.Substituido;

        // Guarda o docId do documento que substituiu o antigo.
        documentos[docId].substituidoPor = novoDocId;

        // Registra publicamente o evento de substituicao.
        emit DocumentoSubstituido(docId, novoDocId);
    }

    // Consulta somente o status atual de um documento.
    function statusAtual(bytes32 docId) external view returns (StatusDocumento) {
        // So permite consultar status de documentos existentes.
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
