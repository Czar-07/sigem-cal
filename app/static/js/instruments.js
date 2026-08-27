/* ============================================================
   SIGEM CAL
   INSTRUMENTOS
   DataTables 2.x
============================================================ */


/* ============================================================
   ESTADO GLOBAL
============================================================ */

let tabelaDevices = null;

let dadosDevices = [];

let filtroAtual = "TODOS";


/* ============================================================
   INICIALIZAÇÃO
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    iniciarPagina
);


/* ============================================================
   INICIAR PÁGINA
============================================================ */

function iniciarPagina() {

    configurarFiltros();

    carregarInstrumentos();

}


/* ============================================================
   CARREGAR INSTRUMENTOS
============================================================ */

async function carregarInstrumentos() {

    try {

        mostrarCarregandoTabela();


        const resposta =
            await fetch(
                "/api/devices",
                {
                    method: "GET",

                    cache: "no-cache",

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


        if (!Array.isArray(dados)) {

            throw new Error(
                "A API não retornou uma lista de instrumentos."
            );

        }


        dadosDevices = dados;


        atualizarContadores();


        renderizarTabela(
            dadosDevices
        );


    }

    catch (erro) {

        console.error(
            "SIGEM CAL — Erro ao carregar instrumentos:",
            erro
        );


        mostrarErroTabela();

    }

}


/* ============================================================
   ATUALIZAR CONTADORES DOS FILTROS
============================================================ */

function atualizarContadores() {

    const total =
        dadosDevices.length;


    const calibrados =
        dadosDevices.filter(
            item =>
                normalizarStatus(item.status) ===
                "CALIBRADO"
        ).length;


    const desenvolvimento =
        dadosDevices.filter(
            item =>
                normalizarStatus(item.status) ===
                "DESENVOLVIMENTO"
        ).length;


    const atrasados =
        dadosDevices.filter(
            item =>
                normalizarStatus(item.status) ===
                "ATRASADO"
        ).length;


    const inativos =
        dadosDevices.filter(
            item =>
                normalizarStatus(item.status) ===
                "INATIVO"
        ).length;


    atualizarElemento(
        "countAll",
        total
    );


    atualizarElemento(
        "countCalibrated",
        calibrados
    );


    atualizarElemento(
        "countDevelopment",
        desenvolvimento
    );


    atualizarElemento(
        "countLate",
        atrasados
    );


    atualizarElemento(
        "countInactive",
        inativos
    );

}

/* ============================================================
   CAPTURAR ESTADO DA TABELA
============================================================ */

function obterEstadoTabela() {

    if (!tabelaDevices) {

        return null;

    }


    return {

        pagina:
            tabelaDevices.page(),

        busca:
            tabelaDevices.search(),

        ordem:
            tabelaDevices.order()

    };

}


/* ============================================================
   RESTAURAR ESTADO DA TABELA
============================================================ */

function restaurarEstadoTabela(
    estado
) {

    if (
        !estado ||
        !tabelaDevices
    ) {

        return;

    }


    /*
     * Restaurar pesquisa.
     */

    if (
        typeof estado.busca === "string"
    ) {

        tabelaDevices.search(
            estado.busca
        );

    }


    /*
     * Restaurar ordenação.
     */

    if (
        Array.isArray(estado.ordem) &&
        estado.ordem.length
    ) {

        tabelaDevices.order(
            estado.ordem
        );

    }


    /*
     * Restaurar página.
     */

    if (
        Number.isInteger(
            estado.pagina
        )
    ) {

        tabelaDevices.page(
            estado.pagina
        );

    }


    /*
     * Aplicar alterações.
     */

    tabelaDevices.draw(
        false
    );

}



/* ============================================================
   RENDERIZAR TABELA
============================================================ */

function renderizarTabela(
    dispositivos
) {

    const estadoTabela =
        obterEstadoTabela();


    const tabela =
        document.querySelector(
            "#devicesTable tbody"
        );


    if (!tabela) {

        console.error(
            "SIGEM CAL — Corpo da tabela não encontrado."
        );

        return;

    }


    /*
     * Se já existe uma instância DataTables,
     * destruímos antes de reconstruir.
     */

    if (tabelaDevices) {

        tabelaDevices.destroy();

        tabelaDevices = null;

    }


    tabela.innerHTML = "";


    /*
     * Caso não existam registros.
     */

    if (!dispositivos.length) {

        inicializarDataTable();

        restaurarEstadoTabela(
            estadoTabela
        );

        return;

    }


    /*
     * Criar linhas.
     */

    dispositivos.forEach(
        item => {

            const linha =
                document.createElement(
                    "tr"
                );


            linha.innerHTML = `

                <td>

                    <a
                        href="/device/${encodeURIComponent(String(item.numero ?? "").trim())}"
                        class="device-link"
                        data-device-id="${escapeHtml(item.numero ?? "")}"
                    >
                        ${escapeHtml(item.numero ?? "-")}
                    </a>

                </td>


                <td>

                    <div class="instrument-name">

                        <strong>

                            ${escapeHtml(
                                item.descricao ?? "-"
                            )}

                        </strong>

                        <span>
                            Instrumento de medição
                        </span>

                    </div>

                </td>


                <td>

                    ${escapeHtml(
                        item.cliente ?? "-"
                    )}

                </td>


                <td>

                    ${escapeHtml(
                        item.part_number ?? "-"
                    )}

                </td>


                <td>

                    ${formatarData(
                        item.proxima_calibracao
                    )}

                </td>


                <td>

                    ${statusColorido(
                        item.status
                    )}

                </td>

                <td class="certificate-cell">

                    <button
                        type="button"
                        class="certificate-action js-device-certificates"
                        title="Visualizar certificados deste dispositivo"
                        data-device-id="${escapeHtml(item.id ?? "")}"
                        data-device-number="${escapeHtml(item.numero ?? "")}"
                    >
                        <i class="bi bi-file-earmark-pdf"></i>
                        <span>Certificados</span>
                    </button>

                </td>

                <td class="qr-cell">
                    ${(() => {
                        const qr = item.qr_code_url || `/device/${encodeURIComponent(item.numero || "")}/qrcode.png`;
                        return `
                            <button type="button" class="qr-action js-qr-device" title="Visualizar QR Code" data-numero="${escapeHtml(item.numero ?? "")}">
                                <i class="bi bi-qr-code-scan"></i>
                            </button>
                            <img class="qr-thumb js-qr-thumb" src="${escapeHtml(qr)}" alt="QR ${escapeHtml(item.numero ?? "")}" data-numero="${escapeHtml(item.numero ?? "")}" loading="lazy">
                        `;
                    })()}
                </td>

            `;


            tabela.appendChild(
                linha
            );

        }
    );


    inicializarDataTable();


    /*
     * Restaurar pesquisa,
     * ordenação e página.
     */

    restaurarEstadoTabela(
        estadoTabela
    );

}




/* ============================================================
   DATATABLES 2.x
============================================================ */

function normalizarLinhasDataTable() {

    const tbody = document.querySelector("#devicesTable tbody");
    if (!tbody) return;

    tbody.querySelectorAll("tr").forEach(linha => {
        const celulas = linha.querySelectorAll("td");
        // Linhas de estado (loading/erro) usam colspan e não devem ser
        // interpretadas como dados pelo DataTables.
        if (celulas.length === 1 && celulas[0].hasAttribute("colspan")) return;

        // A tabela possui exatamente 8 colunas. Evita que uma linha
        // incompleta provoque o warning "Requested unknown parameter '7'".
        while (linha.children.length < 8) {
            const td = document.createElement("td");
            td.textContent = "-";
            linha.appendChild(td);
        }
        while (linha.children.length > 8) {
            linha.removeChild(linha.lastElementChild);
        }
    });
}


function inicializarDataTable() {

    /*
     * Evita criar uma segunda instância.
     */

    if (
        typeof DataTable === "undefined"
    ) {

        console.error(
            "SIGEM CAL — DataTables não foi carregado."
        );

        return;

    }


    if (tabelaDevices) {

        tabelaDevices.destroy();

        tabelaDevices = null;

    }


    // Garante que todas as linhas tenham a mesma estrutura do cabeçalho.
    normalizarLinhasDataTable();

    tabelaDevices =
        new DataTable(
            "#devicesTable",
            {

                /* ====================================================
                   PAGINAÇÃO
                ==================================================== */

                pageLength: 15,


                lengthMenu: [

                    [15, 25, 50, 100],

                    [15, 25, 50, 100]

                ],


                /* ====================================================
                   ORDENAÇÃO
                ==================================================== */

                order: [

                    [0, "asc"]

                ],

                // Se algum dado opcional vier ausente, o DataTables não
                // interrompe a renderização da linha.
                columnDefs: [
                    { targets: "_all", defaultContent: "-" }
                ],


                /* ====================================================
                   LAYOUT DATATABLES 2.x
                ==================================================== */

                layout: {

                    topStart: "pageLength",

                    topEnd: "search",

                    bottomStart: "info",

                    bottomEnd: "paging"

                },


                /* ====================================================
                   IDIOMA
                ==================================================== */

                language: {

                    /*
                     * Texto do campo de pesquisa.
                     */

                    search: "",


                    searchPlaceholder:
                        "Pesquisar instrumento...",


                    /*
                     * Seletor:
                     *
                     * Mostrar 15 registros
                     */

                    lengthMenu:
                        "Mostrar _MENU_ registros",


                    /*
                     * Rodapé:
                     *
                     * Mostrando 1 até 15 de 720
                     */

                    info:
                        "Mostrando _START_ até _END_ de _TOTAL_",


                    /*
                     * Quando não existem registros.
                     */

                    infoEmpty:
                        "Mostrando 0 até 0 de 0",


                    /*
                     * Quando existe pesquisa/filtro.
                     */

                    infoFiltered:
                        "(filtrado de _MAX_ registros)",


                    /*
                     * Nenhum resultado de pesquisa.
                     */

                    zeroRecords:
                        "Nenhum instrumento encontrado",


                    /*
                     * Tabela vazia.
                     */

                    emptyTable:
                        "Nenhum instrumento cadastrado",


                    /*
                     * Paginação.
                     */

                    paginate: {

                        first:
                            "Primeiro",

                        last:
                            "Último",

                        next:
                            "Próximo",

                        previous:
                            "Anterior"

                    }

                }

            }
        );


    /*
     * Configura os links depois
     * da tabela ser criada.
     */


}


/* ============================================================
   FILTROS
============================================================ */

function configurarFiltros() {

    const botoes =
        document.querySelectorAll(
            ".filter-button"
        );


    if (!botoes.length) {

        return;

    }


    botoes.forEach(
        botao => {

            botao.addEventListener(
                "click",
                () => {

                    /*
                     * Remover active de todos.
                     */

                    botoes.forEach(
                        item => {

                            item.classList.remove(
                                "active"
                            );

                        }
                    );


                    /*
                     * Ativar botão clicado.
                     */

                    botao.classList.add(
                        "active"
                    );


                    /*
                     * Obter status.
                     */

                    filtroAtual =
                        String(
                            botao.dataset.status ||
                            "TODOS"
                        )
                        .trim()
                        .toUpperCase();


                    /*
                     * Aplicar filtro.
                     */

                    filtrarTabela(
                        filtroAtual
                    );

                }
            );

        }
    );

}


/* ============================================================
   FILTRAR TABELA
============================================================ */

function filtrarTabela(
    status
) {

    const normalizado =
        String(
            status || "TODOS"
        )
        .trim()
        .toUpperCase();


    /*
     * TODOS
     */

    if (
        normalizado === "TODOS"
    ) {

        renderizarTabela(
            dadosDevices
        );

        return;

    }


    /*
     * Filtrar registros.
     */

    const filtrados =
        dadosDevices.filter(
            item => {

                return (
                    normalizarStatus(
                        item.status
                    ) === normalizado
                );

            }
        );


    /*
     * Renderizar resultado.
     */

    renderizarTabela(
        filtrados
    );

}


/* ============================================================
   NORMALIZAR STATUS
============================================================ */

function normalizarStatus(
    status
) {

    return String(
        status ?? ""
    )
    .trim()
    .toUpperCase();

}


/* ============================================================
   STATUS COLORIDO
============================================================ */

function statusColorido(
    status
) {

    const normalizado =
        normalizarStatus(
            status
        )
        .toLowerCase();


    const statusMap = {

        calibrado: {

            classe:
                "status-calibrado",

            icone:
                "bi-check-circle-fill",

            texto:
                "Calibrado"

        },


        desenvolvimento: {

            classe:
                "status-desenvolvimento",

            icone:
                "bi-hourglass-split",

            texto:
                "Desenvolvimento"

        },


        atrasado: {

            classe:
                "status-atrasado",

            icone:
                "bi-exclamation-triangle-fill",

            texto:
                "Atrasado"

        },


        inativo: {

            classe:
                "status-inativo",

            icone:
                "bi-slash-circle-fill",

            texto:
                "Inativo"

        }

    };


    const configuracao =
        statusMap[
            normalizado
        ];


    /*
     * Status desconhecido.
     */

    if (!configuracao) {

        return `

            <span
                class="status-badge status-desconhecido"
            >

                ${escapeHtml(
                    status || "Não informado"
                )}

            </span>

        `;

    }


    /*
     * Status conhecido.
     */

    return `

        <span
            class="status-badge ${configuracao.classe}"
        >

            <i
                class="bi ${configuracao.icone}"
                aria-hidden="true"
            ></i>

            ${configuracao.texto}

        </span>

    `;

}


/* ============================================================
   FORMATAR DATA
============================================================ */

function formatarData(
    data
) {

    if (
        data === null ||
        data === undefined ||
        data === ""
    ) {

        return "-";

    }


    const valor =
        String(
            data
        ).trim();


    /*
     * Formato esperado:
     *
     * YYYY-MM-DD
     */

    if (
        /^\d{4}-\d{2}-\d{2}$/.test(
            valor
        )
    ) {

        const [
            ano,
            mes,
            dia
        ] =
            valor.split("-");


        return `${dia}/${mes}/${ano}`;

    }


    /*
     * Caso a API já envie
     * outro formato.
     */

    return escapeHtml(
        valor
    );

}


/* ============================================================
   ESCAPE HTML
============================================================ */

function escapeHtml(
    valor
) {

    return String(
        valor
    )

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
        valor;

}


/* ============================================================
   ESTADO — CARREGANDO
============================================================ */

function mostrarCarregandoTabela() {

    const tabela =
        document.querySelector(
            "#devicesTable tbody"
        );


    if (!tabela) {

        return;

    }


    tabela.innerHTML = `

        <tr>

            <td
                colspan="8"
                class="table-error"
            >

                <i
                    class="bi bi-arrow-repeat"
                ></i>

                Carregando instrumentos...

            </td>

        </tr>

    `;

}


/* ============================================================
   ESTADO — ERRO
============================================================ */

function mostrarErroTabela() {

    /*
     * Destruir DataTable caso exista.
     */

    if (tabelaDevices) {

        tabelaDevices.destroy();

        tabelaDevices = null;

    }


    const tabela =
        document.querySelector(
            "#devicesTable tbody"
        );


    if (!tabela) {

        return;

    }


    tabela.innerHTML = `

        <tr>

            <td
                colspan="8"
                class="table-error"
            >

                <i
                    class="bi bi-exclamation-circle"
                    aria-hidden="true"
                ></i>

                Não foi possível carregar
                os instrumentos.

            </td>

        </tr>

    `;

}


/* ============================================================
   SINCRONIZAÇÃO AUTOMÁTICA
============================================================ */

if (window.SIGEMSync) {

    SIGEMSync.onChange(
        async function (dados) {

            console.log(
                "[INSTRUMENTOS] Alteração detectada.",
                dados
            );


            try {

                /*
                 * Recarrega os dados diretamente
                 * da API.
                 */

                await carregarInstrumentos();


                /*
                 * Reaplica o filtro que estava
                 * selecionado pelo usuário.
                 */

                filtrarTabela(
                    filtroAtual
                );


                console.log(
                    "[INSTRUMENTOS] Tabela atualizada com sucesso."
                );


            } catch (erro) {

                console.error(
                    "[INSTRUMENTOS] Erro ao sincronizar:",
                    erro
                );

            }

        }
    );

}

/* ============================================================
   CERTIFICADOS + QR CODE ADMINISTRATIVO
============================================================ */

function abrirCertificadosDispositivo(item) {
    const modalElement = document.getElementById("deviceCertificatesModal");
    const list = document.getElementById("deviceCertificatesList");
    const loading = document.getElementById("deviceCertificatesLoading");
    const empty = document.getElementById("deviceCertificatesEmpty");
    const error = document.getElementById("deviceCertificatesError");
    const errorText = document.getElementById("deviceCertificatesErrorText");
    const subtitle = document.getElementById("deviceCertificatesSubtitle");
    const count = document.getElementById("deviceCertificatesCount");
    if (!modalElement || !list) return;

    subtitle.textContent = `DC ${item.numero || "—"} • ${item.descricao || "Dispositivo de medição"}`;
    list.innerHTML = "";
    list.classList.add("d-none");
    loading.classList.remove("d-none");
    empty.classList.add("d-none");
    error.classList.add("d-none");
    count.textContent = "";

    if (window.bootstrap) bootstrap.Modal.getOrCreateInstance(modalElement).show();

    fetch(`/api/certificates?device_id=${encodeURIComponent(item.id)}`, {
        headers: { "Accept": "application/json" },
        cache: "no-cache"
    })
        .then(async response => {
            const data = await response.json().catch(() => ({}));
            if (!response.ok || data.success === false) {
                throw new Error(data.message || `Erro HTTP ${response.status}`);
            }
            return Array.isArray(data.certificados) ? data.certificados : [];
        })
        .then(certificados => {
            loading.classList.add("d-none");
            if (!certificados.length) {
                empty.classList.remove("d-none");
                count.textContent = "Nenhum certificado vinculado";
                return;
            }
            list.innerHTML = certificados.map(certificadoCard).join("");
            list.classList.remove("d-none");
            count.textContent = `${certificados.length} ${certificados.length === 1 ? "certificado encontrado" : "certificados encontrados"}`;
        })
        .catch(err => {
            console.error("SIGEM CAL — Erro ao carregar certificados do dispositivo:", err);
            loading.classList.add("d-none");
            error.classList.remove("d-none");
            errorText.textContent = err.message || "Não foi possível consultar os certificados.";
        });
}

function certificadoCard(certificado) {
    const situacao = situacaoCertificado(certificado.data_validade);
    const arquivo = String(certificado.nome_arquivo || certificado.arquivo || "");
    const extensao = arquivo.toLowerCase().endsWith(".xlsx") ? "XLSX" : "PDF";
    const numero = certificado.numero_certificado || `#${certificado.id}`;
    const nome = certificado.nome_arquivo || `Certificado ${numero}`;
    return `
        <article class="device-certificate-card">
            <div class="device-certificate-icon"><i class="bi ${extensao === "PDF" ? "bi-file-earmark-pdf" : "bi-file-earmark-excel"}"></i></div>
            <div class="device-certificate-main">
                <div class="device-certificate-top">
                    <strong title="${escapeHtml(nome)}">${escapeHtml(nome)}</strong>
                    <span class="certificate-status ${situacao.classe}">${situacao.texto}</span>
                </div>
                <div class="device-certificate-meta">
                    <span><strong>Certificado:</strong> ${escapeHtml(numero)}</span>
                    <span><strong>Ano:</strong> ${escapeHtml(certificado.ano ?? "—")}</span>
                    <span><strong>Emissão:</strong> ${formatarData(certificado.data_emissao)}</span>
                    <span><strong>Validade:</strong> ${formatarData(certificado.data_validade)}</span>
                </div>
                <small>${escapeHtml(certificado.laboratorio || "Laboratório não informado")} • ${extensao}</small>
            </div>
            <div class="device-certificate-actions">
                <a class="btn btn-sm btn-outline-primary" href="/api/certificates/${certificado.id}/view" target="_blank" rel="noopener" title="Visualizar certificado">
                    <i class="bi bi-eye"></i> Ver
                </a>
                <a class="btn btn-sm btn-primary" href="/api/certificates/${certificado.id}/download" title="Baixar certificado">
                    <i class="bi bi-download"></i> Baixar
                </a>
            </div>
        </article>`;
}

function situacaoCertificado(dataValidade) {
    if (!dataValidade) return { texto: "Sem validade", classe: "neutral" };
    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    const validade = new Date(`${dataValidade}T00:00:00`);
    const dias = Math.ceil((validade - hoje) / 86400000);
    if (dias < 0) return { texto: "Vencido", classe: "danger" };
    if (dias <= 30) return { texto: "Vencendo", classe: "warning" };
    return { texto: "Válido", classe: "success" };
}

function abrirQrDispositivo(item) {
    const img = document.getElementById("qrDeviceImage");
    const number = document.getElementById("qrDeviceNumber");
    const desc = document.getElementById("qrDeviceDescription");
    const subtitle = document.getElementById("qrDeviceSubtitle");
    const open = document.getElementById("qrOpenDevice");
    const download = document.getElementById("qrDownload");
    if (!img) return;
    const qr = item.qr_code_url || `/device/${encodeURIComponent(item.numero)}/qrcode.png`;
    const deviceUrl = item.device_url || `/device/${encodeURIComponent(item.numero)}`;
    img.src = `${qr}${qr.includes("?") ? "&" : "?"}v=${Date.now()}`;
    img.alt = `QR Code do dispositivo ${item.numero}`;
    number.textContent = item.numero || "—";
    desc.textContent = item.descricao || "Dispositivo de medição";
    subtitle.textContent = `Identificação digital • ${item.cliente || "Cliente não informado"}`;
    open.href = deviceUrl;
    download.href = qr;
    download.download = `QR-${item.numero || "dispositivo"}.png`;
    if (window.bootstrap) bootstrap.Modal.getOrCreateInstance(document.getElementById("qrDeviceModal")).show();
}

function configurarEventosDispositivos() {
    const tabela = document.getElementById("devicesTable");
    if (!tabela || tabela.dataset.eventsConfigured === "1") return;
    tabela.dataset.eventsConfigured = "1";
    tabela.addEventListener("click", event => {
        const certificado = event.target.closest(".js-device-certificates");
        if (certificado) {
            event.preventDefault();
            const item = dadosDevices.find(d => String(d.id) === String(certificado.dataset.deviceId));
            if (item) abrirCertificadosDispositivo(item);
            return;
        }
        const qr = event.target.closest(".js-qr-device, .js-qr-thumb");
        if (qr) {
            event.preventDefault();
            const item = dadosDevices.find(d => String(d.numero) === String(qr.dataset.numero));
            if (item) abrirQrDispositivo(item);
        }
    });
}

configurarEventosDispositivos();

document.addEventListener("DOMContentLoaded", () => {
    configurarEventosDispositivos();
    const refresh = document.getElementById("refreshDevices");
    if (refresh && refresh.dataset.bound !== "1") {
        refresh.dataset.bound = "1";
        refresh.addEventListener("click", () => carregarInstrumentos());
    }
});

