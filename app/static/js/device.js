/* ============================================================
   DEVICE.JS
   Página de detalhes do dispositivo
============================================================ */


/* ============================================================
   INICIALIZAÇÃO
============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        carregarDispositivo();
        carregarCertificadosPublicos();

    }
);


/* ============================================================
   CARREGAR DISPOSITIVO
============================================================ */

async function carregarDispositivo() {

    try {

        /* ----------------------------------------------------
           Validação do número
        ---------------------------------------------------- */

        if (
            typeof numeroDispositivo === "undefined" ||
            !numeroDispositivo
        ) {

            throw new Error(
                "Número do dispositivo não informado."
            );

        }


        /* ----------------------------------------------------
           Requisição
        ---------------------------------------------------- */

        
        const resposta =
            await fetch(
                `/api/devices/${encodeURIComponent(
                    numeroDispositivo
                )}`,
                {
                    method: "GET",

                    cache: "no-store",

                    headers: {
                        "Accept": "application/json"
                    }
                }
            );




        /* ----------------------------------------------------
           Erro HTTP
        ---------------------------------------------------- */

        if (!resposta.ok) {

            let mensagem =
                "Dispositivo não encontrado.";

            try {

                const erro =
                    await resposta.json();

                if (erro.erro) {

                    mensagem =
                        erro.erro;

                }

            } catch (_) {

                /* resposta não era JSON */

            }

            throw new Error(
                mensagem
            );

        }


        /* ----------------------------------------------------
           JSON
        ---------------------------------------------------- */

        const dispositivo =
            await resposta.json();


        console.log(
            "Dispositivo carregado:",
            dispositivo
        );


        /* ----------------------------------------------------
           Preenchimento
        ---------------------------------------------------- */

        preencherDispositivo(
            dispositivo
        );


    }

    catch (erro) {

        console.error(
            "Erro ao carregar dispositivo:",
            erro
        );


        mostrarErro(
            erro.message
        );

    }

}


/* ============================================================
   PREENCHER DISPOSITIVO
============================================================ */

function preencherDispositivo(
    dispositivo
) {

    /* ========================================================
       CABEÇALHO
    ======================================================== */

    atualizarElemento(
        "deviceNumber",
        dispositivo.numero
    );


    atualizarElemento(
        "deviceNumberLarge",
        dispositivo.numero
    );


    atualizarElemento(
        "deviceDescription",
        dispositivo.descricao
    );


    atualizarElemento(
        "deviceDescriptionLarge",
        dispositivo.descricao
    );


    /* ========================================================
       IDENTIFICAÇÃO
    ======================================================== */

    atualizarElemento(
        "fieldNumero",
        dispositivo.numero
    );


    atualizarElemento(
        "fieldDescricao",
        dispositivo.descricao
    );


    atualizarElemento(
        "fieldCliente",
        dispositivo.cliente
    );


    atualizarElemento(
        "fieldPartNumber",
        dispositivo.part_number
    );


    /* ========================================================
       CALIBRAÇÃO
    ======================================================== */

    atualizarElemento(
        "fieldUltimaCalibracao",
        formatarData(
            dispositivo.ultima_calibracao
        )
    );


    atualizarElemento(
        "fieldProximaCalibracao",
        formatarData(
            dispositivo.proxima_calibracao
        )
    );


    atualizarElemento(
        "fieldCondicao",
        dispositivo.condicao
    );


    atualizarElemento(
        "fieldStatus",
        dispositivo.status
    );


    /* ========================================================
       STATUS PRINCIPAL
    ======================================================== */

    renderizarStatus(
        dispositivo.status
    );


    /* ========================================================
       CONTROLE METROLÓGICO
    ======================================================== */

    preencherControleMetrologico(
        dispositivo
    );


    /* ========================================================
       QR CODE
    ======================================================== */

    configurarQRCode(
        dispositivo.numero
    );

}


/* ============================================================
   CONTROLE METROLÓGICO
============================================================ */

function preencherControleMetrologico(dispositivo) {

    const calibracao =
        dispositivo.calibracao;

    const status =
        String(dispositivo.status || "")
            .trim()
            .toUpperCase();


    /* --------------------------------------------------------
       ELEMENTOS
    -------------------------------------------------------- */

    const elementoDias =
        document.getElementById(
            "fieldDiasRestantes"
        );

    const elementoSituacao =
        document.getElementById(
            "fieldSituacaoCalibracao"
        );

    const elementoCondicao =
        document.getElementById(
            "fieldCondicao"
        );


    /* --------------------------------------------------------
       SEM CALIBRAÇÃO
    -------------------------------------------------------- */

    if (!calibracao) {

        atualizarElemento(
            "fieldDiasRestantes",
            "-"
        );

        atualizarElemento(
            "fieldSituacaoCalibracao",
            "Não informado"
        );

        aplicarClasseDias(
            elementoDias,
            ""
        );

        aplicarClasseCondicao(
            elementoCondicao,
            ""
        );

        aplicarClasseSituacao(
            elementoSituacao,
            ""
        );

        return;

    }


    /* ========================================================
       CALCULAR DIAS
    ======================================================== */

    let diasRestantes =
        calcularDiasParaCalibracao(
            dispositivo.proxima_calibracao
        );


    /* --------------------------------------------------------
       Fallback para API
    -------------------------------------------------------- */

    if (
        diasRestantes === null &&
        calibracao.dias_restantes !== null &&
        calibracao.dias_restantes !== undefined
    ) {

        diasRestantes =
            Number(
                calibracao.dias_restantes
            );

    }


    /* ========================================================
       ATRASADO
    ======================================================== */

    if (
        status === "ATRASADO" ||
        (
            diasRestantes !== null &&
            diasRestantes < 0
        )
    ) {

        const diasAtraso =
            Math.abs(
                Number(diasRestantes) || 0
            );


        /* ----------------------------------------------------
           CONDIÇÃO
        ---------------------------------------------------- */

        atualizarElemento(
            "fieldCondicao",
            "REPROVADO"
        );

        aplicarClasseCondicao(
            elementoCondicao,
            "reprovado"
        );


        /* ----------------------------------------------------
           DIAS EM ATRASO
        ---------------------------------------------------- */

        atualizarElemento(
            "fieldDiasRestantes",
            formatarDiasAtraso(
                diasAtraso
            )
        );

        aplicarClasseDias(
            elementoDias,
            "overdue"
        );


        /* ----------------------------------------------------
           SITUAÇÃO DA CALIBRAÇÃO
        ---------------------------------------------------- */

        atualizarElemento(
            "fieldSituacaoCalibracao",
            formatarSituacaoAtrasada(
                diasAtraso
            )
        );

        aplicarClasseSituacao(
            elementoSituacao,
            "atrasada"
        );


        return;

    }


    /* ========================================================
       CALIBRADO
    ======================================================== */

    if (
        status === "CALIBRADO"
    ) {

        /* ----------------------------------------------------
           CONDIÇÃO
        ---------------------------------------------------- */

        atualizarElemento(
            "fieldCondicao",
            dispositivo.condicao || "APROVADO"
        );

        aplicarClasseCondicao(
            elementoCondicao,
            "aprovado"
        );


        /* ----------------------------------------------------
           DIAS
        ---------------------------------------------------- */

        atualizarElemento(
            "fieldDiasRestantes",
            formatarDiasRestantes(
                diasRestantes
            )
        );


        /* ----------------------------------------------------
           VENCE HOJE
        ---------------------------------------------------- */

        if (
            diasRestantes === 0
        ) {

            atualizarElemento(
                "fieldSituacaoCalibracao",
                "Vence hoje"
            );

            aplicarClasseSituacao(
                elementoSituacao,
                "hoje"
            );

            aplicarClasseDias(
                elementoDias,
                "today"
            );

        }


        /* ----------------------------------------------------
           CALIBRAÇÃO VÁLIDA
        ---------------------------------------------------- */

        else {

            atualizarElemento(
                "fieldSituacaoCalibracao",
                "Calibração válida"
            );

            aplicarClasseSituacao(
                elementoSituacao,
                "valida"
            );

            aplicarClasseDias(
                elementoDias,
                "valid"
            );

        }


        return;

    }


    /* ========================================================
       DESENVOLVIMENTO
    ======================================================== */

    if (
        status === "DESENVOLVIMENTO"
    ) {

        atualizarElemento(
            "fieldCondicao",
            dispositivo.condicao ||
            "EM DESENVOLVIMENTO"
        );

        aplicarClasseCondicao(
            elementoCondicao,
            "desenvolvimento"
        );


        atualizarElemento(
            "fieldDiasRestantes",
            formatarDiasRestantes(
                diasRestantes
            )
        );


        atualizarElemento(
            "fieldSituacaoCalibracao",
            "Em desenvolvimento"
        );

        aplicarClasseSituacao(
            elementoSituacao,
            "desenvolvimento"
        );

        aplicarClasseDias(
            elementoDias,
            ""
        );


        return;

    }


    /* ========================================================
       INATIVO
    ======================================================== */

    if (
        status === "INATIVO"
    ) {

        atualizarElemento(
            "fieldCondicao",
            dispositivo.condicao ||
            "INATIVO"
        );

        aplicarClasseCondicao(
            elementoCondicao,
            "inativo"
        );


        atualizarElemento(
            "fieldDiasRestantes",
            "-"
        );


        atualizarElemento(
            "fieldSituacaoCalibracao",
            "Instrumento inativo"
        );

        aplicarClasseSituacao(
            elementoSituacao,
            "inativo"
        );

        aplicarClasseDias(
            elementoDias,
            ""
        );


        return;

    }


    /* ========================================================
       STATUS DESCONHECIDO
    ======================================================== */

    atualizarElemento(
        "fieldCondicao",
        dispositivo.condicao || "-"
    );


    atualizarElemento(
        "fieldDiasRestantes",
        formatarDiasRestantes(
            diasRestantes
        )
    );


    atualizarElemento(
        "fieldSituacaoCalibracao",
        calibracao.situacao ||
        "Não informado"
    );

}

/* ============================================================
   CALCULAR DIAS PARA CALIBRAÇÃO
============================================================ */

function calcularDiasParaCalibracao(
    dataCalibracao
) {

    if (!dataCalibracao) {

        return null;

    }


    const valor =
        String(dataCalibracao)
            .trim();


    const correspondencia =
        valor.match(
            /^(\d{4})-(\d{2})-(\d{2})/
        );


    if (!correspondencia) {

        return null;

    }


    const ano =
        Number(correspondencia[1]);

    const mes =
        Number(correspondencia[2]);

    const dia =
        Number(correspondencia[3]);


    /* --------------------------------------------------------
       Data da calibração
       Usa UTC para evitar problemas de timezone.
    -------------------------------------------------------- */

    const dataAlvo =
        Date.UTC(
            ano,
            mes - 1,
            dia
        );


    /* --------------------------------------------------------
       Data atual
    -------------------------------------------------------- */

    const agora =
        new Date();


    const hoje =
        Date.UTC(
            agora.getFullYear(),
            agora.getMonth(),
            agora.getDate()
        );


    /* --------------------------------------------------------
       Diferença em dias
    -------------------------------------------------------- */

    const diferenca =
        Math.round(
            (
                dataAlvo - hoje
            ) /
            (
                1000 *
                60 *
                60 *
                24
            )
        );


    return diferenca;

}


/* ============================================================
   DIAS RESTANTES
============================================================ */

/* ============================================================
   FORMATAR DIAS RESTANTES
============================================================ */

function formatarDiasRestantes(
    dias
) {

    if (
        dias === "-" ||
        dias === null ||
        dias === undefined ||
        Number.isNaN(Number(dias))
    ) {

        return "-";

    }


    dias =
        Number(dias);


    if (dias < 0) {

        return formatarDiasAtraso(
            Math.abs(dias)
        );

    }


    if (dias === 0) {

        return "Vence hoje";

    }


    if (dias === 1) {

        return "1 dia restante";

    }


    return `${dias} dias restantes`;

}

/* ============================================================
   FORMATAR DIAS EM ATRASO
============================================================ */

function formatarDiasAtraso(
    dias
) {

    dias =
        Math.abs(
            Number(dias) || 0
        );


    if (dias === 0) {

        return "Atrasado";

    }


    if (dias === 1) {

        return "1 dia em atraso";

    }


    return `${dias} dias em atraso`;

}

/* ============================================================
   FORMATAR SITUAÇÃO ATRASADA
============================================================ */

function formatarSituacaoAtrasada(
    dias
) {

    dias =
        Math.abs(
            Number(dias) || 0
        );


    if (dias === 1) {

        return "Calibração atrasada — 1 dia";

    }


    return `Calibração atrasada — ${dias} dias`;

}

/* ============================================================
   CLASSE DA CONDIÇÃO
============================================================ */

function aplicarClasseCondicao(
    elemento,
    classe
) {

    if (!elemento) {

        return;

    }


    elemento.classList.remove(

        "condition-aprovado",
        "condition-reprovado",
        "condition-desenvolvimento",
        "condition-inativo"

    );


    if (!classe) {

        return;

    }


    elemento.classList.add(
        `condition-${classe}`
    );

}

/* ============================================================
   CLASSE DA SITUAÇÃO
============================================================ */

function aplicarClasseSituacao(
    elemento,
    classe
) {

    if (!elemento) {

        return;

    }


    elemento.classList.remove(

        "calibration-valid",
        "calibration-overdue",
        "calibration-today",
        "calibration-development",
        "calibration-inactive"

    );


    const classes = {

        valida:
            "calibration-valid",

        atrasada:
            "calibration-overdue",

        hoje:
            "calibration-today",

        desenvolvimento:
            "calibration-development",

        inativo:
            "calibration-inactive"

    };


    if (classes[classe]) {

        elemento.classList.add(
            classes[classe]
        );

    }

}


/* ============================================================
   SITUAÇÃO DA CALIBRAÇÃO
============================================================ */

function renderizarSituacaoCalibracao(
    calibracao
) {

    const elemento =
        document.getElementById(
            "calibrationSituation"
        );


    if (!elemento) {

        return;

    }


    const classe =
        calibracao.classe ||
        "sem-data";


    const icone =
        calibracao.icone ||
        "bi-question-circle";


    const texto =
        calibracao.situacao ||
        "Não informado";


    elemento.innerHTML = `

        <span
            class="calibration-status calibration-${escapeHtml(classe)}"
        >

            <i
                class="bi ${escapeHtml(icone)}"
            ></i>

            ${escapeHtml(texto)}

        </span>

    `;

}


/* ============================================================
   STATUS DO DISPOSITIVO
============================================================ */

function renderizarStatus(
    status
) {

    const elemento =
        document.getElementById(
            "deviceStatus"
        );


    if (!elemento) {

        return;

    }


    const normalizado =
        String(status || "")
            .trim()
            .toLowerCase();


    let classe =
        "status-desconhecido";

    let icone =
        "bi-question-circle";

    let texto =
        status ||
        "Não informado";


    /* --------------------------------------------------------
       CALIBRADO
    -------------------------------------------------------- */

    if (
        normalizado === "calibrado"
    ) {

        classe =
            "status-calibrado";

        icone =
            "bi-check-circle-fill";

        texto =
            "Calibrado";

    }


    /* --------------------------------------------------------
       ATRASADO
    -------------------------------------------------------- */

    else if (
        normalizado === "atrasado"
    ) {

        classe =
            "status-atrasado";

        icone =
            "bi-exclamation-triangle-fill";

        texto =
            "Atrasado";

    }


    /* --------------------------------------------------------
       DESENVOLVIMENTO
    -------------------------------------------------------- */

    else if (
        normalizado === "desenvolvimento"
    ) {

        classe =
            "status-desenvolvimento";

        icone =
            "bi-hourglass-split";

        texto =
            "Desenvolvimento";

    }


    /* --------------------------------------------------------
       INATIVO
    -------------------------------------------------------- */

    else if (
        normalizado === "inativo"
    ) {

        classe =
            "status-inativo";

        icone =
            "bi-slash-circle-fill";

        texto =
            "Inativo";

    }


    elemento.innerHTML = `

        <span
            class="status-badge ${classe}"
        >

            <i
                class="bi ${icone}"
            ></i>

            ${escapeHtml(texto)}

        </span>

    `;

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


    const valor =
        String(data)
            .trim();


    /* --------------------------------------------------------
       YYYY-MM-DD
    -------------------------------------------------------- */

    const correspondencia =
        valor.match(
            /^(\d{4})-(\d{2})-(\d{2})$/
        );


    if (!correspondencia) {

        return valor;

    }


    const ano =
        correspondencia[1];

    const mes =
        correspondencia[2];

    const dia =
        correspondencia[3];


    return `${dia}/${mes}/${ano}`;

}


/* ============================================================
   QR CODE
============================================================ */

function configurarQRCode(
    numero
) {

    const qrCode =
        document.querySelector(
            ".device-qr-code"
        );


    if (!qrCode) {

        console.warn(
            "Elemento QR Code não encontrado."
        );

        return;

    }


    if (!numero) {

        qrCode.style.display =
            "none";

        return;

    }


    /* --------------------------------------------------------
       Caminho do QR Code
    -------------------------------------------------------- */

    qrCode.src =
        `/static/qrcodes/${encodeURIComponent(
            numero
        )}.png`;


    qrCode.alt =
        `QR Code do dispositivo ${numero}`;


    qrCode.style.display =
        "block";


    /* --------------------------------------------------------
       Erro de carregamento
    -------------------------------------------------------- */

    qrCode.onerror =
        () => {

            console.warn(
                `QR Code não encontrado para ${numero}.`
            );


            qrCode.style.display =
                "none";

        };

}


/* ============================================================
   ATUALIZAR ELEMENTO
============================================================ */

function atualizarElemento(
    id,
    valor
) {

    const elemento =
        document.getElementById(id);


    if (!elemento) {

        return;

    }


    if (
        valor === null ||
        valor === undefined ||
        valor === ""
    ) {

        elemento.textContent =
            "-";

        return;

    }


    elemento.textContent =
        valor;

}


/* ============================================================
   ESCAPE HTML
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
   ERRO
============================================================ */

function mostrarErro(
    mensagem
) {

    atualizarElemento(
        "deviceNumber",
        "Dispositivo não encontrado"
    );


    atualizarElemento(
        "deviceNumberLarge",
        "Dispositivo não encontrado"
    );


    atualizarElemento(
        "deviceDescription",
        mensagem ||
        "Não foi possível carregar os dados."
    );


    atualizarElemento(
        "deviceDescriptionLarge",
        mensagem ||
        "Não foi possível carregar os dados."
    );


    const campos = [

        "fieldNumero",
        "fieldDescricao",
        "fieldCliente",
        "fieldPartNumber",
        "fieldUltimaCalibracao",
        "fieldProximaCalibracao",
        "fieldDiasRestantes",
        "fieldCondicao",
        "fieldStatus",
        "fieldSituacaoCalibracao"

    ];


    campos.forEach(
        id => {

            atualizarElemento(
                id,
                "-"
            );

        }
    );


    /* --------------------------------------------------------
       Status
    -------------------------------------------------------- */

    const status =
        document.getElementById(
            "deviceStatus"
        );


    if (status) {

        status.innerHTML = `

            <span
                class="
                    status-badge
                    status-desconhecido
                "
            >

                <i
                    class="
                        bi
                        bi-exclamation-circle
                    "
                ></i>

                Erro

            </span>

        `;

    }


    /* --------------------------------------------------------
       QR Code
    -------------------------------------------------------- */

    const qrCode =
        document.querySelector(
            ".device-qr-code"
        );


    if (qrCode) {

        qrCode.style.display =
            "none";

    }

}

/* ============================================================
   CLASSE DOS DIAS
============================================================ */

function aplicarClasseDias(
    elemento,
    classe
) {

    if (!elemento) {

        return;

    }


    elemento.classList.remove(

        "calibration-days-overdue",
        "calibration-days-valid",
        "calibration-days-today"

    );


    const classes = {

        overdue:
            "calibration-days-overdue",

        valid:
            "calibration-days-valid",

        today:
            "calibration-days-today"

    };


    if (
        classes[classe]
    ) {

        elemento.classList.add(
            classes[classe]
        );

    }

}

/* ============================================================
   SIGEM CAL
   SINCRONIZAÇÃO AUTOMÁTICA DO DISPOSITIVO
============================================================ */

if (window.SIGEMSync) {

    SIGEMSync.onChange(
        async function (dados) {

            console.log(
                "[DEVICE] Alteração detectada.",
                dados
            );


            try {

                await carregarDispositivo();


                console.log(
                    "[DEVICE] Dados atualizados com sucesso."
                );


            } catch (erro) {

                console.error(
                    "[DEVICE] Erro ao atualizar dispositivo:",
                    erro
                );

            }

        }
    );

}



/* ============================================================
   CERTIFICADOS PÚBLICOS DO DISPOSITIVO
============================================================ */
async function carregarCertificadosPublicos() {
    const loading = document.getElementById("publicCertificatesLoading");
    const empty = document.getElementById("publicCertificatesEmpty");
    const error = document.getElementById("publicCertificatesError");
    const list = document.getElementById("publicCertificatesList");
    if (!loading || !list || typeof numeroDispositivo === "undefined") return;

    try {
        const resposta = await fetch(`/api/public/devices/${encodeURIComponent(numeroDispositivo)}/certificates`, {
            method: "GET", cache: "no-store", headers: { "Accept": "application/json" }
        });
        if (!resposta.ok) throw new Error("Falha ao consultar certificados");
        const dados = await resposta.json();
        loading.style.display = "none";
        if (!dados.success || !dados.certificados || !dados.certificados.length) {
            empty.style.display = "block";
            return;
        }
        list.innerHTML = dados.certificados.map(cert => {
            const situacaoClass = cert.situacao === "Válido" ? "valid" : cert.situacao === "Vencido" ? "expired" : cert.situacao === "Vence em breve" ? "warning" : "";
            const emissao = cert.data_emissao ? formatarData(cert.data_emissao) : "-";
            const validade = cert.data_validade ? formatarData(cert.data_validade) : "-";
            const numero = cert.numero_certificado || "Certificado";
            const nome = cert.nome_arquivo || `${numero} · ${cert.ano || ""}`;
            return `<article class="public-certificate-card">
                <div class="public-certificate-icon"><i class="bi bi-file-earmark-pdf"></i></div>
                <div class="public-certificate-main">
                    <div class="public-certificate-title"><strong title="${escapeHtmlPublico(nome)}">${escapeHtmlPublico(nome)}</strong><span class="public-certificate-status ${situacaoClass}">${escapeHtmlPublico(cert.situacao || "Sem informação")}</span></div>
                    <div class="public-certificate-meta"><span><b>Certificado:</b> ${escapeHtmlPublico(numero)}</span><span><b>Emissão:</b> ${emissao}</span><span><b>Validade:</b> ${validade}</span>${cert.laboratorio ? `<span><b>Laboratório:</b> ${escapeHtmlPublico(cert.laboratorio)}</span>` : ""}</div>
                </div>
                <div class="public-certificate-actions"><a class="public-certificate-view" href="${cert.view_url}" target="_blank" rel="noopener"><i class="bi bi-eye"></i> Visualizar</a><a class="public-certificate-download" href="${escapeHtmlPublico(cert.download_url)}"download><i class="bi bi-download"></i>Baixar</a></div>
            </article>`;
        }).join("");
        list.style.display = "grid";
    } catch (e) {
        console.error("Erro ao carregar certificados públicos:", e);
        loading.style.display = "none";
        error.style.display = "block";
    }
}

function escapeHtmlPublico(value) {
    return String(value ?? "").replace(/[&<>\"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'\"':"&quot;","'":"&#039;"}[c]));
}
