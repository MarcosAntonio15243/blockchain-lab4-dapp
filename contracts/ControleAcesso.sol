// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

// Contrato responsavel por controlar quais perfis cada endereco possui.
contract ControleAcesso {
    enum Perfil {
        Nenhum,
        Vara,
        PoliciaFederal,
        CompanhiaAerea,
        ConselhoTutelar
    }

    // Endereco que pode administrar os perfis.
    address public administrador;

    // Tabela que liga um endereco da blockchain ao seu perfil.
    mapping(address => Perfil) private perfis;

    event PerfilDefinido(address indexed conta, Perfil perfil);

    // Modificador que restringe uma funcao apenas ao administrador.
    modifier somenteAdministrador() {
        // Interrompe a execucao se quem chamou a funcao nao for o administrador.
        require(msg.sender == administrador, "somente administrador");

        // Continua a execucao da funcao protegida pelo modificador.
        _;
    }

    constructor() {
        // Quem implanta o contrato vira o administrador.
        administrador = msg.sender;

        // O administrador inicial tambem recebe o perfil da Vara.
        perfis[msg.sender] = Perfil.Vara;
    }

    // Define ou altera o perfil de uma conta.
    function definirPerfil(address conta, Perfil perfil) external somenteAdministrador {
        // Salva o perfil informado para o endereco recebido.
        perfis[conta] = perfil;

        emit PerfilDefinido(conta, perfil);
    }

    // // Consulta qual perfil uma conta possui.
    // function perfilDe(address conta) external view returns (Perfil) {
    //     // Retorna o perfil salvo no mapping; se nao houver cadastro, retorna Nenhum.
    //     return perfis[conta];
    // }

    // // Verifica se uma conta possui exatamente o perfil informado.
    // function temPerfil(address conta, Perfil perfil) external view returns (bool) {
    //     // Retorna true se o perfil salvo for igual ao perfil consultado.
    //     return perfis[conta] == perfil;
    // }
}
