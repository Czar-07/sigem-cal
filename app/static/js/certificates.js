/* ============================================================
   SIGEM CAL — CERTIFICADOS
   Gestão profissional de certificados de calibração
============================================================ */

const CERTIFICATES_API = "/api/certificates";
const DEVICES_API = "/api/devices";
const REGISTROS_POR_PAGINA = 15;

let certificados = [];
let certificadosFiltrados = [];
let dispositivos = [];
let paginaAtual = 1;
let certificadoSelecionado = null;
let modoFormulario = "novo";

document.addEventListener("DOMContentLoaded", iniciarCertificados);

async function iniciarCertificados() {
    configurarEventos();
    await sincronizarAutomaticamente();
    await Promise.all([
        carregarDispositivos(),
        carregarResumo(),
        carregarCertificados()
    ]);
}

function configurarEventos() {
    document.getElementById("certificateSearch")?.addEventListener("input", () => {
        paginaAtual = 1;
        aplicarFiltros();
    });

    document.getElementById("certificateYearFilter")?.addEventListener("change", () => {
        paginaAtual = 1;
        aplicarFiltros();
    });

    document.getElementById("certificateResultFilter")?.addEventListener("change", () => {
        paginaAtual = 1;
        aplicarFiltros();
    });

    document.getElementById("certificateStatusFilter")?.addEventListener("change", () => {
        paginaAtual = 1;
        aplicarFiltros();
    });

    document.getElementById("clearCertificateFilters")?.addEventListener("click", limparFiltros);
    document.getElementById("refreshCertificates")?.addEventListener("click", atualizarTudo);
    document.getElementById("syncCertificatesButton")?.addEventListener("click", sincronizarCertificados);
    document.getElementById("newCertificateButton")?.addEventListener("click", abrirNovoCertificado);

    document.getElementById("certificateForm")?.addEventListener("submit", salvarCertificado);
    document.getElementById("certificateFile")?.addEventListener("change", atualizarArquivoSelecionado);
    document.getElementById("certificateDevice")?.addEventListener("change", atualizarDispositivoSelecionado);

    document.getElementById("certificatesTableBody")?.addEventListener("click", tratarAcaoTabela);

    document.querySelectorAll("[data-summary-filter]").forEach(card => {
        card.addEventListener("click", () => {
            const status = card.dataset.summaryFilter;
            const select = document.getElementById("certificateStatusFilter");
            if (select) {
                select.value = status;
                paginaAtual = 1;
                aplicarFiltros();
                document.querySelector(".certificates-card")?.scrollIntoView({ behavior: "smooth", block: "start" });
            }
        });
    });
}

async function atualizarTudo() {
    const botao = document.getElementById("refreshCertificates");
    if (botao) {
        botao.disabled = true;
        botao.classList.add("is-loading");
    }

    try {
        await Promise.all([carregarResumo(), carregarCertificados()]);
        mostrarNotificacao("Certificados atualizados.", "success");
    } catch (erro) {
        mostrarNotificacao(erro.message || "Não foi possível atualizar.", "error");
    } finally {
        if (botao) {
            botao.disabled = false;
            botao.classList.remove("is-loading");
        }
    }
}


async function sincronizarAutomaticamente() {
    const ultima = Number(sessionStorage.getItem("sigem_certificates_last_sync") || 0);
    if (Date.now() - ultima < 5 * 60 * 1000) return;
    try {
        await sincronizarCertificados(false);
    } catch (erro) {
        console.warn("SIGEM CAL — sincronização automática:", erro);
    }
}

async function sincronizarCertificados(mostrarMensagem = true) {
    const botao = document.getElementById("syncCertificatesButton");
    if (botao) { botao.disabled = true; botao.classList.add("is-loading"); }
    try {
        const resposta = await fetch(`${CERTIFICATES_API}/sync`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "application/json" },
            body: JSON.stringify({})
        });
        const texto = await resposta.text();
        let dados = {};
        try { dados = texto ? JSON.parse(texto) : {}; } catch (_) {
            dados = { message: texto || `Erro HTTP ${resposta.status}` };
        }
        if (!resposta.ok || !dados.success) {
            const detalhe = dados.error ? ` — ${dados.error}` : "";
            throw new Error((dados.message || `Erro HTTP ${resposta.status}`) + detalhe);
        }
        sessionStorage.setItem("sigem_certificates_last_sync", String(Date.now()));
        if (mostrarMensagem) {
            mostrarNotificacao(`Sincronização concluída: ${dados.imported || 0} novos, ${dados.updated || 0} alterados, ${dados.unchanged || 0} sem alteração.`, "success");
            await Promise.all([carregarResumo(), carregarCertificados()]);
        }
        if ((dados.unmatched || []).length) {
            console.warn("Certificados sem dispositivo correspondente:", dados.unmatched);
        }
        return dados;
    } finally {
        if (botao) { botao.disabled = false; botao.classList.remove("is-loading"); }
    }
}

async function carregarDispositivos() {
    const select = document.getElementById("certificateDevice");
    if (!select) return;

    try {
        select.innerHTML = `<option value="">Carregando instrumentos...</option>`;
        const resposta = await fetch(DEVICES_API, { headers: { Accept: "application/json" } });
        if (!resposta.ok) throw new Error(`Erro HTTP ${resposta.status}`);

        const dados = await resposta.json();
        dispositivos = Array.isArray(dados) ? dados : (Array.isArray(dados.devices) ? dados.devices : []);
        preencherSelectDispositivos();
    } catch (erro) {
        console.error("SIGEM CAL — dispositivos:", erro);
        select.innerHTML = `<option value="">Não foi possível carregar os instrumentos</option>`;
    }
}

function preencherSelectDispositivos(valorSelecionado = "") {
    const select = document.getElementById("certificateDevice");
    if (!select) return;

    const lista = [...dispositivos].sort((a, b) =>
        String(a.numero || "").localeCompare(String(b.numero || ""), "pt-BR", { numeric: true })
    );

    select.innerHTML = `<option value="">Selecione o dispositivo...</option>`;

    lista.forEach(device => {
        const option = document.createElement("option");
        option.value = device.id;
        option.textContent = `${device.numero || "Sem DC"} — ${device.descricao || "Instrumento"}`;
        select.appendChild(option);
    });

    if (valorSelecionado) {
        select.value = String(valorSelecionado);
        atualizarDispositivoSelecionado();
    }
}

function atualizarDispositivoSelecionado() {
    const select = document.getElementById("certificateDevice");
    const container = document.getElementById("deviceInfoContainer");
    const device = dispositivos.find(item => String(item.id) === String(select?.value));

    if (!device) {
        container?.setAttribute("hidden", "");
        return;
    }

    container?.removeAttribute("hidden");
    atualizarTexto("linkedDeviceNumber", device.numero || "—");
    atualizarTexto("linkedDeviceDescription", device.descricao || "Instrumento");
    atualizarTexto("linkedDeviceClient", device.cliente || "—");
    atualizarTexto("linkedDevicePartNumber", device.part_number || "—");
}

async function carregarResumo() {
    try {
        const resposta = await fetch(`${CERTIFICATES_API}/summary`, {
            headers: { Accept: "application/json" }
        });
        if (!resposta.ok) throw new Error(`Erro HTTP ${resposta.status}`);

        const dados = await resposta.json();
        if (!dados.success) throw new Error(dados.message || "Falha no resumo.");

        const resumo = dados.resumo || {};
        atualizarTexto("certificateTotal", resumo.total ?? 0);
        atualizarTexto("certificateCurrentYear", resumo.ano_atual ?? 0);
        atualizarTexto("certificateValid", resumo.validos ?? 0);
        atualizarTexto("certificateExpiring", resumo.vencendo ?? 0);
        atualizarTexto("certificateExpired", resumo.vencidos ?? 0);
        atualizarTexto("certificateNoValidity", resumo.sem_validade ?? 0);
    } catch (erro) {
        console.error("SIGEM CAL — resumo:", erro);
    }
}

async function carregarCertificados() {
    mostrarCarregandoTabela();

    const resposta = await fetch(CERTIFICATES_API, {
        headers: { Accept: "application/json" }
    });

    if (!resposta.ok) throw new Error(`Erro HTTP ${resposta.status}`);

    const dados = await resposta.json();
    if (!dados.success) throw new Error(dados.message || "Não foi possível carregar.");

    certificados = Array.isArray(dados.certificados) ? dados.certificados : [];
    preencherFiltroAnos();
    paginaAtual = 1;
    aplicarFiltros();
}

function preencherFiltroAnos() {
    const select = document.getElementById("certificateYearFilter");
    if (!select) return;

    const atual = select.value;
    const anos = [...new Set(certificados.map(item => Number(item.ano)).filter(Number.isInteger))]
        .sort((a, b) => b - a);

    select.innerHTML = `<option value="">Todos os anos</option>`;
    anos.forEach(ano => {
        const option = document.createElement("option");
        option.value = ano;
        option.textContent = ano;
        select.appendChild(option);
    });

    if (anos.includes(Number(atual))) select.value = atual;
}

function aplicarFiltros() {
    const pesquisa = (document.getElementById("certificateSearch")?.value || "").trim().toLowerCase();
    const ano = document.getElementById("certificateYearFilter")?.value || "";
    const resultado = document.getElementById("certificateResultFilter")?.value || "";
    const status = document.getElementById("certificateStatusFilter")?.value || "";

    certificadosFiltrados = certificados.filter(certificado => {
        const situacao = calcularSituacao(certificado.data_validade);
        const texto = [
            certificado.numero_certificado,
            certificado.numero,
            certificado.numero_dispositivo,
            certificado.descricao,
            certificado.cliente,
            certificado.part_number,
            certificado.laboratorio,
            certificado.nome_arquivo,
            certificado.ano
        ].filter(Boolean).join(" ").toLowerCase();

        return (
            (!pesquisa || texto.includes(pesquisa)) &&
            (!ano || String(certificado.ano) === String(ano)) &&
            (!resultado || normalizarResultado(certificado.resultado) === resultado) &&
            (!status || situacao.tipo === status)
        );
    });

    const totalPaginas = Math.max(1, Math.ceil(certificadosFiltrados.length / REGISTROS_POR_PAGINA));
    paginaAtual = Math.min(paginaAtual, totalPaginas);
    renderizarTabela();
}

function renderizarTabela() {
    const tbody = document.getElementById("certificatesTableBody");
    if (!tbody) return;

    const inicio = (paginaAtual - 1) * REGISTROS_POR_PAGINA;
    const registros = certificadosFiltrados.slice(inicio, inicio + REGISTROS_POR_PAGINA);

    tbody.innerHTML = registros.length
        ? registros.map(criarLinhaCertificado).join("")
        : `<tr><td colspan="8" class="table-empty">
            <i class="bi bi-search"></i>
            <div>Nenhum certificado encontrado</div>
            <small>Ajuste os filtros ou cadastre um novo certificado.</small>
        </td></tr>`;

    atualizarContador(certificadosFiltrados.length);
    renderizarPaginacao();
}

function criarLinhaCertificado(certificado) {
    const situacao = calcularSituacao(certificado.data_validade);
    const resultado = normalizarResultado(certificado.resultado);
    const numero = certificado.numero_certificado || "Sem número";
    const instrumento = certificado.numero || certificado.numero_dispositivo || "—";
    const descricao = certificado.descricao || "Instrumento";
    const laboratorio = certificado.laboratorio || "Não informado";
    const arquivo = certificado.nome_arquivo || "";

    return `
        <tr>
            <td>
                <div class="certificate-cell">
                    <div class="certificate-file-icon ${certificado.arquivo ? "has-file" : "no-file"}">
                        <i class="bi bi-file-earmark-pdf-fill"></i>
                    </div>
                    <div class="certificate-cell-content">
                        <strong title="${escapeHtml(numero)}">${escapeHtml(numero)}</strong>
                        <small>${escapeHtml(arquivo || `Certificado ${certificado.ano || ""}`)}</small>
                    </div>
                </div>
            </td>
            <td>
                <div class="instrument-cell">
                    <strong>${escapeHtml(instrumento)}</strong>
                    <small>${escapeHtml(descricao)}</small>
                </div>
            </td>
            <td>
                <span class="laboratory-cell" title="${escapeHtml(laboratorio)}">
                    ${escapeHtml(laboratorio)}
                </span>
            </td>
            <td>${formatarData(certificado.data_emissao)}</td>
            <td>
                <div class="validity-cell">
                    <strong>${formatarData(certificado.data_validade)}</strong>
                    ${criarPrazo(situacao)}
                </div>
            </td>
            <td>${criarBadgeResultado(resultado)}</td>
            <td>${criarBadgeSituacao(situacao)}</td>
            <td>
                <div class="certificate-actions">
                    <button type="button" class="certificate-action" data-action="view" data-id="${certificado.id}" title="${certificado.source_type === "pdf" ? "Visualizar PDF" : "Somente download"}" ${certificado.source_type === "pdf" ? "" : "disabled"}>
                        <i class="bi bi-eye"></i>
                    </button>
                    <button type="button" class="certificate-action action-download" data-action="download" data-id="${certificado.id}" title="${certificado.arquivo ? `Baixar ${String(certificado.source_type || "arquivo").toUpperCase()}` : "Sem arquivo"}" ${certificado.arquivo ? "" : "disabled"}>
                        <i class="bi bi-download"></i>
                    </button>
                    <button type="button" class="certificate-action" data-action="edit" data-id="${certificado.id}" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button type="button" class="certificate-action action-delete" data-action="delete" data-id="${certificado.id}" title="Excluir">
                        <i class="bi bi-trash3"></i>
                    </button>
                </div>
            </td>
        </tr>`;
}

function calcularSituacao(data) {
    if (!data) return { tipo: "none", texto: "Sem validade", dias: null };

    const hoje = new Date();
    hoje.setHours(0, 0, 0, 0);
    const validade = new Date(`${data}T00:00:00`);
    const dias = Math.ceil((validade - hoje) / 86400000);

    if (dias < 0) return { tipo: "expired", texto: "Vencido", dias };
    if (dias === 0) return { tipo: "expired", texto: "Vence hoje", dias };
    if (dias <= 30) return { tipo: "expiring", texto: "Vencendo", dias };
    return { tipo: "valid", texto: "Válido", dias };
}

function criarPrazo(situacao) {
    if (situacao.dias === null) return "";
    if (situacao.dias < 0) return `<small class="certificate-deadline warning">${Math.abs(situacao.dias)}d vencido</small>`;
    if (situacao.dias === 0) return `<small class="certificate-deadline warning">Hoje</small>`;
    if (situacao.dias <= 30) return `<small class="certificate-deadline warning">${situacao.dias}d restantes</small>`;
    return `<small class="certificate-deadline safe">${situacao.dias}d restantes</small>`;
}

function criarBadgeSituacao(situacao) {
    const icones = {
        valid: "bi-check-circle-fill",
        expiring: "bi-hourglass-split",
        expired: "bi-exclamation-triangle-fill",
        none: "bi-calendar-x"
    };
    return `<span class="certificate-status ${situacao.tipo}">
        <i class="bi ${icones[situacao.tipo]}"></i>${situacao.texto}
    </span>`;
}

function normalizarResultado(resultado) {
    const valor = String(resultado || "").trim().toLowerCase();
    if (["aprovado", "conforme"].includes(valor)) return "Aprovado";
    if (["reprovado", "não conforme", "nao conforme"].includes(valor)) return "Reprovado";
    return "Não informado";
}

function criarBadgeResultado(resultado) {
    const classe = resultado === "Aprovado" ? "result-approved" :
        resultado === "Reprovado" ? "result-rejected" : "result-unknown";
    const icone = resultado === "Aprovado" ? "bi-check-circle-fill" :
        resultado === "Reprovado" ? "bi-x-circle-fill" : "bi-dash-circle";
    return `<span class="result-badge ${classe}"><i class="bi ${icone}"></i>${resultado}</span>`;
}

function tratarAcaoTabela(event) {
    const botao = event.target.closest("[data-action]");
    if (!botao || botao.disabled) return;

    const id = Number(botao.dataset.id);
    if (!id) return;

    const acoes = {
        view: visualizarCertificado,
        download: baixarCertificado,
        edit: editarCertificado,
        delete: excluirCertificado
    };

    acoes[botao.dataset.action]?.(id);
}

async function visualizarCertificado(id) {

    const certificado = certificados.find(
        item => Number(item.id) === id
    );

    if (!certificado?.arquivo) {
        mostrarNotificacao(
            "Este certificado não possui arquivo.",
            "warning"
        );
        return;
    }

    const modalElement =
        document.getElementById(
            "certificateViewerModal"
        );

    const iframe =
        document.getElementById(
            "certificateViewer"
        );

    const download =
        document.getElementById(
            "viewerDownloadButton"
        );

    if (!modalElement || !iframe) return;

    try {

        mostrarNotificacao(
            "Preparando certificado...",
            "info"
        );

        const resposta = await fetch(
            `${CERTIFICATES_API}/${id}/view`,
            {
                headers: {
                    Accept: "application/json"
                }
            }
        );

        const dados = await resposta.json();

        if (!resposta.ok || !dados.success) {
            throw new Error(
                dados.message ||
                "Não foi possível abrir o certificado."
            );
        }

        iframe.src = dados.url;

        if (download) {

            download.onclick = async () => {

                try {

                    const respostaDownload =
                        await fetch(
                            `${CERTIFICATES_API}/${id}/download`,
                            {
                                headers: {
                                    Accept: "application/json"
                                }
                            }
                        );

                    const dadosDownload =
                        await respostaDownload.json();

                    if (
                        !respostaDownload.ok ||
                        !dadosDownload.success
                    ) {
                        throw new Error(
                            dadosDownload.message ||
                            "Não foi possível baixar o certificado."
                        );
                    }

                    window.open(
                        dadosDownload.url,
                        "_blank",
                        "noopener,noreferrer"
                    );

                } catch (erro) {

                    console.error(
                        "SIGEM CAL — download:",
                        erro
                    );

                    mostrarNotificacao(
                        erro.message,
                        "error"
                    );
                }
            };
        }

        atualizarTexto(
            "certificateViewerTitle",
            certificado.numero_certificado ||
            `Certificado ${certificado.ano || ""}`
        );

        abrirModal(
            "certificateViewerModal"
        );

    } catch (erro) {

        console.error(
            "SIGEM CAL — visualização:",
            erro
        );

        mostrarNotificacao(
            erro.message ||
            "Não foi possível visualizar o certificado.",
            "error"
        );
    }
}

async function baixarCertificado(id) {

    try {

        const resposta = await fetch(
            `${CERTIFICATES_API}/${id}/download`,
            {
                headers: {
                    Accept: "application/json"
                }
            }
        );

        const dados = await resposta.json();

        if (!resposta.ok || !dados.success) {
            throw new Error(
                dados.message ||
                "Não foi possível baixar o certificado."
            );
        }

        window.open(
            dados.url,
            "_blank",
            "noopener,noreferrer"
        );

    } catch (erro) {

        console.error(
            "SIGEM CAL — download:",
            erro
        );

        mostrarNotificacao(
            erro.message ||
            "Não foi possível baixar o certificado.",
            "error"
        );
    }
}

function abrirNovoCertificado() {
    modoFormulario = "novo";
    certificadoSelecionado = null;
    limparFormulario();
    preencherSelectDispositivos();
    alterarTituloModal("Novo certificado");

    const ano = document.getElementById("certificateYear");
    if (ano) ano.value = new Date().getFullYear();

    abrirModal("certificateModal");
}

async function editarCertificado(id) {
    try {
        const resposta = await fetch(`${CERTIFICATES_API}/${id}`, { headers: { Accept: "application/json" } });
        const dados = await resposta.json();
        if (!resposta.ok || !dados.success) throw new Error(dados.message || "Certificado não encontrado.");

        certificadoSelecionado = dados.certificado;
        modoFormulario = "editar";
        preencherSelectDispositivos(certificadoSelecionado.device_id);
        preencherFormulario(certificadoSelecionado);
        alterarTituloModal("Editar certificado");
        abrirModal("certificateModal");
    } catch (erro) {
        console.error(erro);
        mostrarNotificacao(erro.message, "error");
    }
}

function preencherFormulario(certificado) {
    definirValor("certificateId", certificado.id);
    definirValor("certificateDevice", certificado.device_id);
    definirValor("certificateYear", certificado.ano);
    definirValor("certificateNumber", certificado.numero_certificado);
    definirValor("certificateIssueDate", certificado.data_emissao);
    definirValor("certificateExpirationDate", certificado.data_validade);
    definirValor("certificateLaboratory", certificado.laboratorio);
    definirValor("certificateResult", certificado.resultado);
    definirValor("certificateObservations", certificado.observacoes);
    atualizarDispositivoSelecionado();

    const arquivo = document.getElementById("selectedCertificateFile");
    if (arquivo) {
        arquivo.innerHTML = certificado.nome_arquivo
            ? `<i class="bi bi-file-earmark-pdf"></i> Arquivo atual: <strong>${escapeHtml(certificado.nome_arquivo)}</strong>`
            : `<span>Nenhum PDF vinculado.</span>`;
    }
}

function limparFormulario() {
    const formulario = document.getElementById("certificateForm");
    formulario?.reset();
    definirValor("certificateId", "");

    const arquivo = document.getElementById("selectedCertificateFile");
    if (arquivo) arquivo.innerHTML = `<span>Nenhum arquivo selecionado.</span>`;

    document.getElementById("deviceInfoContainer")?.setAttribute("hidden", "");
}

async function salvarCertificado(event) {
    event.preventDefault();

    const formulario = document.getElementById("certificateForm");
    if (!formulario) return;

    if (!formulario.checkValidity()) {
        formulario.classList.add("was-validated");
        formulario.reportValidity();
        return;
    }

    const formData = new FormData(formulario);
    const id = formData.get("certificateId");
    const arquivo = formData.get("arquivo");

    bloquearBotaoSalvar(true);

    try {
        let resposta;

        if (arquivo instanceof File && arquivo.size > 0) {
            const endpoint = id ? `${CERTIFICATES_API}/${id}/upload` : `${CERTIFICATES_API}/upload`;
            resposta = await fetch(endpoint, { method: "POST", body: formData });
        } else if (id) {
            const dados = criarObjetoFormulario(formData);
            resposta = await fetch(`${CERTIFICATES_API}/${id}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json", Accept: "application/json" },
                body: JSON.stringify(dados)
            });
        } else {
            resposta = await fetch(CERTIFICATES_API, {
                method: "POST",
                headers: { "Content-Type": "application/json", Accept: "application/json" },
                body: JSON.stringify(criarObjetoFormulario(formData))
            });
        }

        const dados = await resposta.json();
        if (!resposta.ok || !dados.success) throw new Error(dados.message || "Não foi possível salvar.");

        fecharModal("certificateModal");
        mostrarNotificacao(id ? "Certificado atualizado com sucesso." : "Certificado cadastrado com sucesso.", "success");
        await Promise.all([carregarResumo(), carregarCertificados()]);
    } catch (erro) {
        console.error("SIGEM CAL — salvar:", erro);
        mostrarNotificacao(erro.message || "Não foi possível salvar.", "error");
    } finally {
        bloquearBotaoSalvar(false);
    }
}

function criarObjetoFormulario(formData) {
    return {
        device_id: Number(formData.get("device_id")),
        ano: Number(formData.get("ano")),
        numero_certificado: formData.get("numero_certificado") || null,
        data_emissao: formData.get("data_emissao") || null,
        data_validade: formData.get("data_validade") || null,
        laboratorio: formData.get("laboratorio") || null,
        resultado: formData.get("resultado") || null,
        observacoes: formData.get("observacoes") || null
    };
}

async function excluirCertificado(id) {
    const certificado = certificados.find(item => Number(item.id) === id);
    const identificacao = certificado?.numero_certificado || `#${id}`;

    if (!confirm(`Excluir o certificado ${identificacao}?\n\nEsta ação não pode ser desfeita.`)) return;

    try {
        const resposta = await fetch(`${CERTIFICATES_API}/${id}`, { method: "DELETE", headers: { Accept: "application/json" } });
        const dados = await resposta.json();
        if (!resposta.ok || !dados.success) throw new Error(dados.message || "Não foi possível excluir.");

        mostrarNotificacao("Certificado excluído com sucesso.", "success");
        await Promise.all([carregarResumo(), carregarCertificados()]);
    } catch (erro) {
        mostrarNotificacao(erro.message, "error");
    }
}

function limparFiltros() {
    const search = document.getElementById("certificateSearch");
    const year = document.getElementById("certificateYearFilter");
    const result = document.getElementById("certificateResultFilter");
    const status = document.getElementById("certificateStatusFilter");

    if (search) search.value = "";
    if (year) year.value = "";
    if (result) result.value = "";
    if (status) status.value = "";

    paginaAtual = 1;
    aplicarFiltros();
}

function renderizarPaginacao() {
    const container = document.getElementById("certificatePagination");
    if (!container) return;

    const totalPaginas = Math.ceil(certificadosFiltrados.length / REGISTROS_POR_PAGINA);
    container.innerHTML = "";
    if (totalPaginas <= 1) return;

    const criarBotao = (label, pagina, disabled = false, ativo = false) => {
        const botao = document.createElement("button");
        botao.type = "button";
        botao.className = `pagination-button ${ativo ? "active" : ""}`;
        botao.disabled = disabled;
        botao.innerHTML = label;
        if (!disabled) {
            botao.addEventListener("click", () => {
                paginaAtual = pagina;
                renderizarTabela();
            });
        }
        return botao;
    };

    container.appendChild(criarBotao(`<i class="bi bi-chevron-left"></i>`, paginaAtual - 1, paginaAtual === 1));

    const paginas = construirPaginas(totalPaginas, paginaAtual);
    paginas.forEach(item => {
        if (item === "...") {
            const span = document.createElement("span");
            span.className = "pagination-ellipsis";
            span.textContent = "…";
            container.appendChild(span);
        } else {
            container.appendChild(criarBotao(String(item), item, false, item === paginaAtual));
        }
    });

    container.appendChild(criarBotao(`<i class="bi bi-chevron-right"></i>`, paginaAtual + 1, paginaAtual === totalPaginas));
}

function construirPaginas(total, atual) {
    if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);

    const base = new Set([1, total, atual, atual - 1, atual + 1]);
    const ordenadas = [...base].filter(n => n >= 1 && n <= total).sort((a, b) => a - b);
    const resultado = [];

    ordenadas.forEach((n, index) => {
        if (index && n - ordenadas[index - 1] > 1) resultado.push("...");
        resultado.push(n);
    });

    return resultado;
}

function atualizarContador(quantidade) {
    const elemento = document.getElementById("certificateResultCount");
    if (!elemento) return;

    elemento.innerHTML = `<strong>${quantidade}</strong> ${quantidade === 1 ? "certificado encontrado" : "certificados encontrados"}`;
}

function atualizarArquivoSelecionado(event) {
    const arquivo = event.target.files?.[0];
    const elemento = document.getElementById("selectedCertificateFile");
    if (!elemento) return;

    if (!arquivo) {
        elemento.innerHTML = `<span>Nenhum arquivo selecionado.</span>`;
        return;
    }

    if (!arquivo.name.toLowerCase().endsWith(".pdf")) {
        event.target.value = "";
        elemento.innerHTML = `<span class="file-error">Apenas arquivos PDF são permitidos.</span>`;
        mostrarNotificacao("Selecione um arquivo PDF.", "warning");
        return;
    }

    const max = 20 * 1024 * 1024;
    if (arquivo.size > max) {
        event.target.value = "";
        elemento.innerHTML = `<span class="file-error">O arquivo excede o limite de 20 MB.</span>`;
        mostrarNotificacao("O PDF excede o limite de 20 MB.", "warning");
        return;
    }

    elemento.innerHTML = `<i class="bi bi-file-earmark-pdf"></i> <strong>${escapeHtml(arquivo.name)}</strong> <span>• ${formatarTamanho(arquivo.size)}</span>`;
}

function formatarTamanho(bytes) {
    if (!bytes) return "0 KB";
    const mb = bytes / 1048576;
    return mb >= 1 ? `${mb.toFixed(2)} MB` : `${Math.round(bytes / 1024)} KB`;
}

function formatarData(data) {
    if (!data) return "—";
    const [ano, mes, dia] = String(data).slice(0, 10).split("-");
    if (!ano || !mes || !dia) return "—";
    return `${dia}/${mes}/${ano}`;
}

function definirValor(id, valor) {
    const elemento = document.getElementById(id);
    if (elemento) elemento.value = valor ?? "";
}

function atualizarTexto(id, valor) {
    const elemento = document.getElementById(id);
    if (elemento) elemento.textContent = valor;
}

function escapeHtml(valor) {
    return String(valor ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function abrirModal(id) {
    const elemento = document.getElementById(id);
    if (!elemento || typeof bootstrap === "undefined") return;
    bootstrap.Modal.getOrCreateInstance(elemento).show();
}

function fecharModal(id) {
    const elemento = document.getElementById(id);
    if (!elemento || typeof bootstrap === "undefined") return;
    bootstrap.Modal.getInstance(elemento)?.hide();
}

function alterarTituloModal(titulo) {
    atualizarTexto("certificateModalTitle", titulo);
}

function bloquearBotaoSalvar(bloquear) {
    const botao = document.getElementById("saveCertificateButton");
    if (!botao) return;

    botao.disabled = bloquear;
    botao.innerHTML = bloquear
        ? `<span class="spinner-border spinner-border-sm me-2" aria-hidden="true"></span> Salvando...`
        : `<i class="bi bi-check-lg"></i> Salvar certificado`;
}

function mostrarCarregandoTabela() {
    const tbody = document.getElementById("certificatesTableBody");
    if (!tbody) return;
    tbody.innerHTML = `<tr><td colspan="8" class="table-loading">
        <div class="loading-content"><span class="spinner-border spinner-border-sm"></span> Carregando certificados...</div>
    </td></tr>`;
}

function mostrarNotificacao(mensagem, tipo = "info") {
    if (typeof window.showToast === "function") {
        window.showToast(mensagem, tipo);
        return;
    }

    const container = document.getElementById("toastContainer") || (() => {
        const el = document.createElement("div");
        el.id = "toastContainer";
        el.className = "certificate-toast-container";
        document.body.appendChild(el);
        return el;
    })();

    const toast = document.createElement("div");
    toast.className = `certificate-toast ${tipo}`;
    toast.innerHTML = `<i class="bi bi-${tipo === "success" ? "check-circle" : tipo === "error" ? "x-circle" : "info-circle"}"></i><span>${escapeHtml(mensagem)}</span>`;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3500);
}
