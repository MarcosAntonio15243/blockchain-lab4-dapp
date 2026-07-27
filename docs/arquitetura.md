# Arquitetura da solução

```mermaid
flowchart LR
    U[Usuário] --> F[Frontend]
    F --> C[Contrato na blockchain]
    F --> O[(Armazenamento off-chain)]
```