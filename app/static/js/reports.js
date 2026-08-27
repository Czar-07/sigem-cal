/* ============================================================
   SIGEM CAL
   RELATÓRIOS
============================================================ */


/* ============================================================
   INICIALIZAÇÃO
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        carregarResumo();

        carregarClientes();

        configurarTipos();

        configurarAcoes();

    }
);


/* ============================================================
   ESTADO DO RELATÓRIO
============================================================ */

function obterEstadoRelatorio() {

    return {

        tipo:
            obterTipoRelatorio(),

        cliente:
            document.getElementById(
                "reportClient"
            )?.value || "todos",

        status:
            document.getElementById(
                "reportStatus"
            )?.value || "todos",

        periodo:
            document.getElementById(
                "reportPeriod"
            )?.value || "current"

    };

}


/* ============================================================
   RESTAURAR ESTADO DO RELATÓRIO
============================================================ */

function restaurarEstadoRelatorio(
    estado
) {

    if (!estado) {

        return;

    }


    /*
     * Restaurar tipo.
     */

    const tipos =
        document.querySelectorAll(
            ".report-type"
        );


    tipos.forEach(
        tipo => {

            const ativo =
                tipo.dataset.report ===
                estado.tipo;


            tipo.classList.toggle(
                "active",
                ativo
            );

        }
    );


    /*
     * Restaurar cliente.
     */

    const cliente =
        document.getElementById(
            "reportClient"
        );


    if (cliente) {

        cliente.value =
            estado.cliente;

    }


    /*
     * Restaurar status.
     */

    const status =
        document.getElementById(
            "reportStatus"
        );


    if (status) {

        status.value =
            estado.status;

    }


    /*
     * Restaurar período.
     */

    const periodo =
        document.getElementById(
            "reportPeriod"
        );


    if (periodo) {

        periodo.value =
            estado.periodo;

    }

}


/* ============================================================
   RESUMO
============================================================ */

async function carregarResumo() {

    try {

 
    const resposta =
        await fetch(
            "/api/reports/summary",
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
                `Erro HTTP ${resposta.status}`
            );

        }


        const dados =
            await resposta.json();


        if (!dados.success) {

            throw new Error(
                "Resumo indisponível."
            );

        }


        const resumo =
            dados.resumo;


        atualizarElemento(
            "reportTotal",
            resumo.total
        );


        atualizarElemento(
            "reportCalibrated",
            resumo.calibrados
        );


        atualizarElemento(
            "reportExpiring",
            resumo.vencendo_30
        );


        atualizarElemento(
            "reportOverdue",
            resumo.atrasados
        );

    }

    catch (erro) {

        console.error(
            "Erro ao carregar resumo:",
            erro
        );

    }

}


/* ============================================================
   CLIENTES
============================================================ */

async function carregarClientes() {

    const select =
        document.getElementById(
            "reportClient"
        );


    if (!select) {

        return;

    }


    try {

        select.disabled = true;


        const resposta =
            await fetch(
                "/api/reports/clients",
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
                `Erro HTTP ${resposta.status}`
            );

        }


        const dados =
            await resposta.json();


        if (!dados.success) {

            throw new Error(
                "Não foi possível carregar os clientes."
            );

        }


        const clientes =
            Array.isArray(
                dados.clientes
            )
                ? dados.clientes
                : [];


        /* ----------------------------------------------------
           LIMPAR SELECT
        ---------------------------------------------------- */

        select.innerHTML = "";


        /* ----------------------------------------------------
           TODOS OS CLIENTES
        ---------------------------------------------------- */

        const opcaoTodos =
            document.createElement(
                "option"
            );


        opcaoTodos.value =
            "todos";


        opcaoTodos.textContent =
            "Todos os clientes";


        select.appendChild(
            opcaoTodos
        );


        /* ----------------------------------------------------
           CLIENTES VINDOS DO BANCO
        ---------------------------------------------------- */

        clientes.forEach(
            cliente => {

                const opcao =
                    document.createElement(
                        "option"
                    );


                opcao.value =
                    cliente;


                opcao.textContent =
                    cliente;


                select.appendChild(
                    opcao
                );

            }
        );

    }

    catch (erro) {

        console.error(
            "Erro ao carregar clientes:",
            erro
        );


        /*
         * Mesmo que a API falhe,
         * mantemos a opção padrão.
         */

        select.innerHTML = `

            <option value="todos">
                Todos os clientes
            </option>

        `;

    }

    finally {

        select.disabled = false;

    }

}


/* ============================================================
   TIPOS DE RELATÓRIO
============================================================ */

function configurarTipos() {

    const tipos =
        document.querySelectorAll(
            ".report-type"
        );


    tipos.forEach(
        tipo => {

            tipo.addEventListener(
                "click",
                () => {

                    tipos.forEach(
                        item => {

                            item.classList.remove(
                                "active"
                            );

                        }
                    );


                    tipo.classList.add(
                        "active"
                    );

                }
            );

        }
    );

}


/* ============================================================
   OBTER TIPO DO RELATÓRIO
============================================================ */

function obterTipoRelatorio() {

    const ativo =
        document.querySelector(
            ".report-type.active"
        );


    if (!ativo) {

        return "calibrations";

    }


    return (
        ativo.dataset.report ||
        "calibrations"
    );

}


/* ============================================================
   OBTER FILTROS
============================================================ */

function obterFiltros() {

    const cliente =
        document.getElementById(
            "reportClient"
        );


    const status =
        document.getElementById(
            "reportStatus"
        );


    const periodo =
        document.getElementById(
            "reportPeriod"
        );


    return {

        tipo:
            obterTipoRelatorio(),

        cliente:
            cliente
                ? cliente.value
                : "todos",

        status:
            status
                ? status.value
                : "todos",

        periodo:
            periodo
                ? periodo.value
                : "current"

    };

}


/* ============================================================
   CONSTRUIR URL DO RELATÓRIO
============================================================ */

function construirUrlRelatorio() {

    const filtros =
        obterFiltros();


    const parametros =
        new URLSearchParams();


    /* --------------------------------------------------------
       TIPO
    -------------------------------------------------------- */

    parametros.set(
        "tipo",
        filtros.tipo
    );


    /* --------------------------------------------------------
       CLIENTE
    -------------------------------------------------------- */

    parametros.set(
        "cliente",
        filtros.cliente
    );


    /* --------------------------------------------------------
       STATUS
    -------------------------------------------------------- */

    parametros.set(
        "status",
        filtros.status
    );


    /* --------------------------------------------------------
       PERÍODO
    -------------------------------------------------------- */

    parametros.set(
        "periodo",
        filtros.periodo
    );


    return (
        `/api/reports/pdf?${parametros.toString()}`
    );

}


/* ============================================================
   CONFIGURAR AÇÕES
============================================================ */

function configurarAcoes() {

    const gerar =
        document.getElementById(
            "generateReport"
        );


    const visualizar =
        document.getElementById(
            "previewReport"
        );


    if (gerar) {

        gerar.addEventListener(
            "click",
            gerarPDF
        );

    }


    if (visualizar) {

        visualizar.addEventListener(
            "click",
            visualizarPDF
        );

    }

}


/* ============================================================
   GERAR PDF
============================================================ */

function gerarPDF() {

    const botao =
        document.getElementById(
            "generateReport"
        );


    if (!botao) {

        return;

    }


    /* --------------------------------------------------------
       URL
    -------------------------------------------------------- */

    const url =
        construirUrlRelatorio();


    /* --------------------------------------------------------
       DESABILITAR BOTÃO
    -------------------------------------------------------- */

    botao.disabled = true;


    botao.innerHTML = `

        <i class="bi bi-arrow-repeat"></i>

        Gerando PDF...

    `;


    /* --------------------------------------------------------
       ABRIR PDF
    -------------------------------------------------------- */

    window.open(
        url,
        "_blank"
    );


    /* --------------------------------------------------------
       RESTAURAR BOTÃO
    -------------------------------------------------------- */

    setTimeout(
        () => {

            botao.disabled = false;


            botao.innerHTML = `

                <i class="bi bi-file-earmark-pdf"></i>

                Gerar PDF

            `;

        },
        1200
    );

}


/* ============================================================
   VISUALIZAR PDF
============================================================ */

function visualizarPDF() {

    const url =
        construirUrlRelatorio();


    window.open(
        url,
        "_blank"
    );

}


/* ============================================================
   ATUALIZAR ELEMENTO
============================================================ */

function atualizarElemento(
    id,
    valor
) {

    const elemento =
        document.getElementById(
            id
        );


    if (!elemento) {

        return;

    }


    elemento.textContent =
        valor ?? "-";

}

/* ============================================================
   SINCRONIZAÇÃO AUTOMÁTICA
============================================================ */

if (window.SIGEMSync) {

    SIGEMSync.onChange(
        async function (dados) {

            console.log(
                "[RELATÓRIOS] Alteração detectada.",
                dados
            );


            /*
             * Guardar filtros atuais.
             */

            const estado =
                obterEstadoRelatorio();


            try {

                /*
                 * Atualizar resumo.
                 */

                await carregarResumo();


                /*
                 * Atualizar lista de clientes.
                 */

                await carregarClientes();


                /*
                 * Restaurar filtros.
                 */

                restaurarEstadoRelatorio(
                    estado
                );


                console.log(
                    "[RELATÓRIOS] Dados atualizados com sucesso."
                );

            }

            catch (erro) {

                console.error(
                    "[RELATÓRIOS] Erro na sincronização:",
                    erro
                );

            }

        }
    );

}