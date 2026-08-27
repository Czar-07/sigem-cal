let charts = {};

document.addEventListener("DOMContentLoaded", carregarDashboard);

async function carregarDashboard() {
    try {
        const response = await fetch("/api/dashboard", { cache: "no-store", headers: {"Accept":"application/json"} });
        const data = await response.json();
        if (!response.ok || !data.success) throw new Error(data.message || "Falha ao carregar dashboard.");
        atualizarIndicadores(data);
        atualizarGraficos(data);
    } catch (error) {
        console.error("[DASHBOARD]", error);
        window.showToast?.(error.message, "danger");
    }
}

function text(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}

function atualizarIndicadores(d) {
    text("totalDevices", d.total ?? 0);
    text("activeDevices", d.ativos ?? 0);
    text("calibratedDevices", d.calibrado ?? 0);
    text("expiringDevices", d.vencendo ?? 0);
    text("lateDevices", d.vencidos ?? 0);
    text("noDateDevices", d.sem_data ?? 0);
    text("calibratedPercentage", `${Number(d.ativos) ? ((Number(d.calibrado)/Number(d.ativos))*100).toFixed(1) : "0.0"}%`);
    text("compliancePercentage", `${Number(d.conformidade || 0).toFixed(1)}%`);
    text("syncSource", `Fonte: ${d.sync?.source || "system"}`);
    const bar = document.getElementById("complianceProgress");
    if (bar) bar.style.width = `${Math.max(0, Math.min(100, Number(d.conformidade || 0)))}%`;
    const sync = d.sync?.updated_at;
    text("lastSync", sync ? new Date(sync).toLocaleString("pt-BR") : "—");
}

function makeChart(id, config) {
    const canvas = document.getElementById(id);
    if (!canvas || typeof Chart === "undefined") return;
    if (charts[id]) charts[id].destroy();
    charts[id] = new Chart(canvas, config);
}

const baseOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { labels: { usePointStyle: true, boxWidth: 8, font: { family: "Inter", size: 10 } } } }
};

function atualizarGraficos(d) {
    const status = d.status || {};
    makeChart("statusChart", {
        type: "doughnut",
        data: { labels: ["Calibrados","Desenvolvimento","Atrasados","Inativos"], datasets: [{ data: [status.calibrado||0,status.desenvolvimento||0,status.atrasado||0,status.inativo||0], borderWidth: 3 }] },
        options: {...baseOptions, cutout:"70%", plugins:{...baseOptions.plugins, legend:{position:"bottom", labels:{usePointStyle:true, padding:16,font:{family:"Inter",size:10}}}}}
    });

    const clients = d.clientes || {labels:[],data:[]};
    makeChart("clientChart", {
        type:"bar",
        data:{labels:clients.labels,datasets:[{label:"Instrumentos",data:clients.data,borderRadius:6}]},
        options:{...baseOptions,indexAxis:"y",plugins:{legend:{display:false}},scales:{x:{beginAtZero:true,ticks:{precision:0}},y:{grid:{display:false}}}}
    });

    const conditions = d.condicoes || {labels:[],data:[]};
    makeChart("conditionChart", {
        type:"bar",
        data:{labels:conditions.labels,datasets:[{label:"Dispositivos",data:conditions.data,borderRadius:6}]},
        options:{...baseOptions,plugins:{legend:{display:false}},scales:{x:{grid:{display:false}},y:{beginAtZero:true,ticks:{precision:0}}}}
    });

    const cert = d.certificados || {};
    makeChart("certificateChart", {
        type:"bar",
        data:{labels:["Certificado 2025","Certificado 2026","Sem certificado 2026"],datasets:[{label:"Dispositivos",data:[cert["2025"]||0,cert["2026"]||0,cert.sem_2026||0],borderRadius:6}]},
        options:{...baseOptions,plugins:{legend:{display:false}},scales:{x:{grid:{display:false}},y:{beginAtZero:true,ticks:{precision:0}}}}
    });

    const cal = d.calibracoes_por_mes || {labels:[],data:[]};
    makeChart("calibrationChart", {
        type:"line",
        data:{labels:cal.labels,datasets:[{label:"Calibrações previstas",data:cal.data,borderWidth:2,tension:.35,fill:true}]},
        options:{...baseOptions,interaction:{intersect:false,mode:"index"},plugins:{legend:{display:false}},scales:{x:{grid:{display:false}},y:{beginAtZero:true,ticks:{precision:0}}}}
    });
}

window.addEventListener("sigem:sync-complete", carregarDashboard);
window.addEventListener("sigem:data-changed", carregarDashboard);
if (window.SIGEMSync) SIGEMSync.onChange(carregarDashboard);
