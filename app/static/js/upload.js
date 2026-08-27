document.addEventListener("DOMContentLoaded", () => {
    const button = document.getElementById("uploadExcelButton");
    const form = document.getElementById("excelUploadForm");
    const modalEl = document.getElementById("excelUploadModal");
    if (!button || !form || !modalEl || !window.bootstrap) return;

    const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
    const progress = document.getElementById("excelUploadProgress");
    const submit = document.getElementById("excelUploadSubmit");

    button.addEventListener("click", () => modal.show());

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const file = document.getElementById("excelFile")?.files?.[0];
        if (!file) return;
        const payload = new FormData();
        payload.append("file", file);
        submit.disabled = true;
        progress?.classList.remove("d-none");
        try {
            const response = await fetch("/api/sync/upload", { method: "POST", body: payload });
            const data = await response.json();
            if (!response.ok || !data.success) throw new Error(data.message || "Falha ao importar Excel.");
            window.showToast?.(`${data.message} ${data.resultado?.inseridos || 0} novos, ${data.resultado?.atualizados || 0} atualizados.`, "success");
            modal.hide();
            form.reset();
            window.dispatchEvent(new CustomEvent("sigem:sync-complete", { detail: data }));
            window.dispatchEvent(new CustomEvent("sigem:data-changed", { detail: data }));
        } catch (error) {
            window.showToast?.(error.message || "Não foi possível importar o Excel.", "danger");
        } finally {
            submit.disabled = false;
            progress?.classList.add("d-none");
        }
    });
});
