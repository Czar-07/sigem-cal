/* ============================================================
   SIGEM CAL
   SISTEMA GLOBAL DE SINCRONIZAÇÃO
   ============================================================ */

(function () {

    "use strict";


    /* ========================================================
       CONFIGURAÇÃO
       ======================================================== */

    const CONFIG = {

        endpoint: "/api/sync/version",

        interval: 3000,

        storageKey: "sigem_sync_version"

    };


    /* ========================================================
       ESTADO
       ======================================================== */

    let versaoAtual = null;

    let executando = false;


    /* ========================================================
       EVENTO GLOBAL
       ======================================================== */

    function emitirEventoSincronizacao(dados) {

        const evento = new CustomEvent(
            "sigem:data-changed",
            {
                detail: dados
            }
        );

        window.dispatchEvent(
            evento
        );
    }


    /* ========================================================
       CONSULTAR SERVIDOR
       ======================================================== */

    async function consultarVersao() {

        if (executando) {

            return;

        }

        executando = true;


        try {

            const resposta = await fetch(
                CONFIG.endpoint,
                {
                    method: "GET",

                    cache: "no-store",

                    headers: {
                        "Accept": "application/json"
                    }
                }
            );


            if (!resposta.ok) {

                throw new Error(
                    `HTTP ${resposta.status}`
                );

            }


            const dados = await resposta.json();


            if (!dados.success) {

                throw new Error(
                    "Servidor retornou success=false."
                );

            }


            processarVersao(
                dados
            );


        } catch (erro) {

            console.error(
                "[SIGEM SYNC] Erro:",
                erro
            );


        } finally {

            executando = false;

        }
    }


    /* ========================================================
       PROCESSAR VERSÃO
       ======================================================== */

    function processarVersao(dados) {

        const novaVersao = Number(
            dados.version
        );


        if (!Number.isFinite(novaVersao)) {

            console.warn(
                "[SIGEM SYNC] Versão inválida:",
                dados.version
            );

            return;

        }


        /* ----------------------------------------------------
           PRIMEIRA LEITURA
           ---------------------------------------------------- */

        if (versaoAtual === null) {

            versaoAtual = novaVersao;

            localStorage.setItem(
                CONFIG.storageKey,
                String(novaVersao)
            );


            console.info(
                "[SIGEM SYNC] Versão inicial:",
                novaVersao
            );


            return;

        }


        /* ----------------------------------------------------
           NENHUMA ALTERAÇÃO
           ---------------------------------------------------- */

        if (novaVersao === versaoAtual) {

            return;

        }


        /* ----------------------------------------------------
           ALTERAÇÃO DETECTADA
           ---------------------------------------------------- */

        const versaoAnterior =
            versaoAtual;


        versaoAtual =
            novaVersao;


        localStorage.setItem(
            CONFIG.storageKey,
            String(novaVersao)
        );


        console.info(
            "[SIGEM SYNC] Alteração detectada:",
            versaoAnterior,
            "→",
            novaVersao
        );


        emitirEventoSincronizacao({

            version: novaVersao,

            previousVersion:
                versaoAnterior,

            source:
                dados.source,

            updatedAt:
                dados.updated_at

        });

    }


    /* ========================================================
       INICIALIZAÇÃO
       ======================================================== */

    function iniciar() {

        console.info(
            "[SIGEM SYNC] Sistema iniciado."
        );


        consultarVersao();


        setInterval(
            consultarVersao,
            CONFIG.interval
        );

    }


    /* ========================================================
       API PÚBLICA
       ======================================================== */

    window.SIGEMSync = {

        getVersion: function () {

            return versaoAtual;

        },


        check: function () {

            return consultarVersao();

        },


        onChange: function (callback) {

            window.addEventListener(
                "sigem:data-changed",
                function (evento) {

                    callback(
                        evento.detail
                    );

                }
            );

        }

    };


    /* ========================================================
       START
       ======================================================== */

    if (
        document.readyState === "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            iniciar
        );

    } else {

        iniciar();

    }

})();
