/* ============================================================
   SIGEM CAL
   CALIBRATIONS.JS
============================================================ */


let calibracoes = [];

let filtroAtual = "todos";

let paginaAtual = 1;

const registrosPorPagina = 15;


/* ============================================================
   INICIALIZAÇÃO
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        carregarCalibracoes();

        configurarPesquisa();

        configurarFiltros();

    }
);


/* ============================================================
   ESTADO DA TABELA
============================================================ */

function obterEstadoCalibracoes() {

    const input =
        document.getElementById(
            "calibrationSearch"
        );


    return {

        filtro:
            filtroAtual,

        pagina:
            paginaAtual,

        pesquisa:
            input?.value || ""

    };

}


/* ============================================================
   RESTAURAR ESTADO
============================================================ */

function restaurarEstadoCalibracoes(
    estado
) {

    if (!estado) {

        return;

    }


    /*
     * Restaurar filtro.
     */

    filtroAtual =
        estado.filtro ||
        "todos";


    /*
     * Restaurar pesquisa.
     */

    const input =
        document.getElementById(
            "calibrationSearch"
        );


    if (input) {

        input.value =
            estado.pesquisa || "";

    }


    /*
     * Recalcular quantidade de páginas
     * depois que os novos dados chegaram.
     */

    const total =
        obterRegistrosFiltrados().length;


    const paginas =
        Math.max(
            1,
            Math.ceil(
                total /
                registrosPorPagina
            )
        );


    /*
     * Não permitir que a página
     * restaurada fique além do total.
     */

    paginaAtual =
        Math.min(
            estado.pagina || 1,
            paginas
        );

}




/* ============================================================
   CARREGAR
============================================================ */

async function carregarCalibracoes(
    preservarEstado = false
) {

    /*
     * Guardar estado antes de buscar
     * os novos dados.
     */

    const estadoAnterior =
        preservarEstado
            ? obterEstadoCalibracoes()
            : null;


    try {

        const resposta =
            await fetch(
                "/api/calibrations",
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
                "Não foi possível carregar as calibrações."
            );

        }


        /*
         * Atualizar dados.
         */

        calibracoes =
            dados.calibracoes || [];


        /*
         * Atualizar resumo.
         */

        atualizarResumo(
            dados.resumo
        );


        /*
         * Restaurar pesquisa,
         * filtro e página.
         */

        if (estadoAnterior) {

            restaurarEstadoCalibracoes(
                estadoAnterior
            );

        }


        /*
         * Renderizar tabela.
         */

        renderizarTabela();


    }

    catch (erro) {

        console.error(
            "Erro ao carregar calibrações:",
            erro
        );


        mostrarErroTabela();

    }

}




/* ============================================================
   RESUMO
============================================================ */

function atualizarResumo(
    resumo
) {

    atualizarElemento(
        "totalCalibrations",
        resumo.total
    );


    atualizarElemento(
        "validCalibrations",
        resumo.validas
    );


    atualizarElemento(
        "expiringCalibrations",
        resumo.vencendo
    );


    atualizarElemento(
        "overdueCalibrations",
        resumo.atrasadas
    );

}


/* ============================================================
   PESQUISA
============================================================ */

function configurarPesquisa() {

    const input =
        document.getElementById(
            "calibrationSearch"
        );


    if (!input) {

        return;

    }


    input.addEventListener(
        "input",
        () => {

            paginaAtual = 1;

            renderizarTabela();

        }
    );

}


/* ============================================================
   FILTROS
============================================================ */

function configurarFiltros() {

    const botoes =
        document.querySelectorAll(
            ".filter-button"
        );


    botoes.forEach(
        botao => {

            botao.addEventListener(
                "click",
                () => {

                    botoes.forEach(
                        item => {

                            item.classList.remove(
                                "active"
                            );

                        }
                    );


                    botao.classList.add(
                        "active"
                    );


                    filtroAtual =
                        botao.dataset.filter;


                    paginaAtual = 1;


                    renderizarTabela();

                }
            );

        }
    );

}


/* ============================================================
   FILTRAR
============================================================ */

function obterRegistrosFiltrados() {

    const input =
        document.getElementById(
            "calibrationSearch"
        );


    const pesquisa =
        String(
            input?.value || ""
        )
            .trim()
            .toLowerCase();


    return calibracoes.filter(
        item => {

            /* -----------------------------------------------
               FILTRO DE SITUAÇÃO
            ----------------------------------------------- */

            if (
                filtroAtual !== "todos" &&
                item.classe !== filtroAtual
            ) {

                return false;

            }


            /* -----------------------------------------------
               PESQUISA
            ----------------------------------------------- */

            if (!pesquisa) {

                return true;

            }


            const texto = [

                item.numero,

                item.descricao,

                item.cliente,

                item.part_number

            ]
                .filter(Boolean)
                .join(" ")
                .toLowerCase();


            return texto.includes(
                pesquisa
            );

        }
    );

}


/* ============================================================
   TABELA
============================================================ */

function renderizarTabela() {

    const tbody =
        document.getElementById(
            "calibrationTableBody"
        );


    if (!tbody) {

        return;

    }


    const registros =
        obterRegistrosFiltrados();


    const total =
        registros.length;


    const inicio =
        (
            paginaAtual - 1
        ) *
        registrosPorPagina;


    const fim =
        inicio +
        registrosPorPagina;


    const pagina =
        registros.slice(
            inicio,
            fim
        );


    tbody.innerHTML = "";


    if (!pagina.length) {

        tbody.innerHTML = `

            <tr>

                <td
                    colspan="8"
                    class="table-empty"
                >

                    <i class="bi bi-search"></i>

                    Nenhuma calibração encontrada.

                </td>

            </tr>

        `;

        atualizarRodape(
            total
        );

        renderizarPaginacao(
            total
        );

        return;

    }


    pagina.forEach(
        dispositivo => {

            tbody.insertAdjacentHTML(
                "beforeend",
                criarLinha(
                    dispositivo
                )
            );

        }
    );


    atualizarRodape(
        total
    );


    renderizarPaginacao(
        total
    );

}


/* ============================================================
   LINHA
============================================================ */

function criarLinha(
    dispositivo
) {

    const prazo =
        formatarPrazo(
            dispositivo.dias_restantes
        );


    const situacao =
        criarBadgeSituacao(
            dispositivo
        );


    return `

        <tr>

            <td class="device-number">

                ${escapeHtml(
                    dispositivo.numero || "-"
                )}

            </td>


            <td>

                <div class="instrument-cell">

                    <strong>

                        ${escapeHtml(
                            dispositivo.descricao || "-"
                        )}

                    </strong>

                    <small>

                        ${escapeHtml(
                            dispositivo.part_number || ""
                        )}

                    </small>

                </div>

            </td>


            <td>

                ${escapeHtml(
                    dispositivo.cliente || "-"
                )}

            </td>


            <td>

                ${formatarData(
                    dispositivo.ultima_calibracao
                )}

            </td>


            <td>

                ${formatarData(
                    dispositivo.proxima_calibracao
                )}

            </td>


            <td>

                <span
                    class="deadline ${obterClassePrazo(
                        dispositivo.dias_restantes
                    )}"
                >

                    ${prazo}

                </span>

            </td>


            <td>

                ${situacao}

            </td>


            <td class="col-action">

                <a
                    href="/device/${encodeURIComponent(
                        dispositivo.numero
                    )}"
                    class="view-device"
                    title="Ver dispositivo"
                >

                    <i class="bi bi-arrow-up-right"></i>

                </a>

            </td>

        </tr>

    `;

}


/* ============================================================
   SITUAÇÃO
============================================================ */

function criarBadgeSituacao(
    dispositivo
) {

    const classe =
        dispositivo.classe || "sem-data";


    const icones = {

        valida:
            "bi-check-circle-fill",

        vencendo:
            "bi-hourglass-split",

        hoje:
            "bi-exclamation-circle-fill",

        atrasada:
            "bi-exclamation-triangle-fill",

        "sem-data":
            "bi-question-circle"

    };


    const icone =
        icones[classe] ||
        icones["sem-data"];


    return `

        <span
            class="
                calibration-badge
                calibration-${escapeHtml(classe)}
            "
        >

            <i
                class="bi ${icone}"
            ></i>

            ${escapeHtml(
                dispositivo.situacao || "Sem data"
            )}

        </span>

    `;

}


/* ============================================================
   PRAZO
============================================================ */

function formatarPrazo(
    dias
) {

    if (
        dias === null ||
        dias === undefined
    ) {

        return "-";

    }


    dias =
        Number(dias);


    if (dias < 0) {

        const atraso =
            Math.abs(dias);


        return atraso === 1
            ? "1 dia em atraso"
            : `${atraso} dias em atraso`;

    }


    if (dias === 0) {

        return "Hoje";

    }


    if (dias === 1) {

        return "1 dia";

    }


    return `${dias} dias`;

}


/* ============================================================
   CLASSE PRAZO
============================================================ */

function obterClassePrazo(
    dias
) {

    if (
        dias === null ||
        dias === undefined
    ) {

        return "deadline-none";

    }


    dias =
        Number(dias);


    if (dias < 0) {

        return "deadline-overdue";

    }


    if (dias === 0) {

        return "deadline-today";

    }


    if (dias <= 30) {

        return "deadline-warning";

    }


    return "deadline-valid";

}


/* ============================================================
   DATA
============================================================ */

function formatarData(
    data
) {

    if (!data) {

        return "-";

    }


    const match =
        String(data).match(
            /^(\d{4})-(\d{2})-(\d{2})/
        );


    if (!match) {

        return data;

    }


    return `${match[3]}/${match[2]}/${match[1]}`;

}


/* ============================================================
   PAGINAÇÃO
============================================================ */

function renderizarPaginacao(
    total
) {

    const container =
        document.getElementById(
            "calibrationPagination"
        );


    if (!container) {

        return;

    }


    const paginas =
        Math.ceil(
            total /
            registrosPorPagina
        );


    container.innerHTML = "";


    if (paginas <= 1) {

        return;

    }


    for (
        let i = 1;
        i <= paginas;
        i++
    ) {

        const botao =
            document.createElement(
                "button"
            );


        botao.type =
            "button";


        botao.textContent =
            i;


        botao.className =
            "pagination-button";


        if (
            i === paginaAtual
        ) {

            botao.classList.add(
                "active"
            );

        }


        botao.addEventListener(
            "click",
            () => {

                paginaAtual = i;

                renderizarTabela();

                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });

            }
        );


        container.appendChild(
            botao
        );

    }

}


/* ============================================================
   RODAPÉ
============================================================ */

function atualizarRodape(
    total
) {

    const elemento =
        document.getElementById(
            "tableResultCount"
        );


    if (!elemento) {

        return;

    }


    elemento.textContent =
        total === 1
            ? "1 registro"
            : `${total} registros`;

}


/* ============================================================
   ERRO
============================================================ */

function mostrarErroTabela() {

    const tbody =
        document.getElementById(
            "calibrationTableBody"
        );


    if (!tbody) {

        return;

    }


    tbody.innerHTML = `

        <tr>

            <td
                colspan="8"
                class="table-error"
            >

                <i class="bi bi-exclamation-circle"></i>

                Não foi possível carregar as calibrações.

            </td>

        </tr>

    `;

}


/* ============================================================
   ELEMENTO
============================================================ */

function atualizarElemento(
    id,
    valor
) {

    const elemento =
        document.getElementById(
            id
        );


    if (elemento) {

        elemento.textContent =
            valor ?? "-";

    }

}


/* ============================================================
   ESCAPE
============================================================ */

function escapeHtml(
    valor
) {

    return String(valor)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );

}


/* ============================================================
   SINCRONIZAÇÃO AUTOMÁTICA
============================================================ */

if (window.SIGEMSync) {

    SIGEMSync.onChange(
        async function (dados) {

            console.log(
                "[CALIBRAÇÕES] Alteração detectada.",
                dados
            );


            try {

                /*
                 * Buscar novamente os dados
                 * mantendo o estado da tela.
                 */

                await carregarCalibracoes(
                    true
                );


                console.log(
                    "[CALIBRAÇÕES] Dados atualizados com sucesso."
                );


            } catch (erro) {

                console.error(
                    "[CALIBRAÇÕES] Erro na sincronização:",
                    erro
                );

            }

        }
    );

}

