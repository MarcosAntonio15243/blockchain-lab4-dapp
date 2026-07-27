# Contratos inteligentes - VerificaJus Sigilo

## Diagrama de classes

```mermaid
classDiagram
    direction LR

    class ControleAcesso {
        +address administrador
        +mapping(address => Perfil) perfis
        +definirPerfil(address conta, Perfil perfil) void
        +perfilDe(address conta) Perfil
        +temPerfil(address conta, Perfil perfil) bool
    }

    class RegistroDocumentos {
        +address vara
        +ControleAcesso controleAcesso
        +mapping(bytes32 => Documento) documentos
        +registrarDocumento(bytes32 docId, bytes32 hashDocumento, string tipoDocumento, string orgaoEmissor, uint256 validoAte) void
        +documentoExiste(bytes32 docId) bool
        +verificarDocumento(bytes32 docId) DocumentoView
        +revogarDocumento(bytes32 docId) void
        +substituirDocumento(bytes32 docId, bytes32 novoDocId) void
        +statusAtual(bytes32 docId) StatusDocumento
    }

    class Documento {
        +bytes32 hashDocumento
        +string tipoDocumento
        +string orgaoEmissor
        +uint256 emitidoEm
        +uint256 validoAte
        +StatusDocumento status
        +bytes32 substituidoPor
        +bool existe
    }

    class StatusDocumento {
        <<enumeration>>
        Valido
        Expirado
        Revogado
        Substituido
    }

    class Perfil {
        <<enumeration>>
        Nenhum
        Vara
        PoliciaFederal
        CompanhiaAerea
        ConselhoTutelar
    }

    RegistroDocumentos --> ControleAcesso : consulta perfis
    RegistroDocumentos *-- Documento : armazena
    Documento --> StatusDocumento : possui
    ControleAcesso --> Perfil : atribui
```

## Responsabilidades

| Contrato | Responsabilidade |
|---|---|
| `RegistroDocumentos` | Registrar documentos sigilosos por hash, consultar existencia, retornar status e manter eventos auditaveis do ciclo de vida |
| `ControleAcesso` | Manter perfis institucionais que poderao ser usados pela aplicacao para filtrar informacoes exibidas |

## Funcao central desta entrega

A funcao relevante implementada nesta versao e `registrarDocumento`, que grava na blockchain o identificador aleatorio do documento, o hash do PDF e metadados minimos. A funcao `documentoExiste` permite verificar se um `docId` ja foi registrado.

O contrato ainda nao implementa todas as validacoes de producao. Controle fino de permissao, tratamento de casos de borda, integracao com QR Code e exibicao seletiva completa ficam para as proximas entregas.
