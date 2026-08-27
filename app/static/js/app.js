document.addEventListener("DOMContentLoaded", () => {
    const sidebar = document.getElementById("sidebar");
    const backdrop = document.getElementById("sidebarBackdrop");
    const toggle = document.querySelector("[data-sidebar-toggle]");
    const search = document.getElementById("globalSearch");
    const sync = document.getElementById("syncNowButton");

    const closeMenu = () => {
        sidebar?.classList.remove("open");
        backdrop?.classList.remove("show");
    };
    toggle?.addEventListener("click", () => {
        sidebar?.classList.toggle("open");
        backdrop?.classList.toggle("show");
    });
    backdrop?.addEventListener("click", closeMenu);
    sidebar?.querySelectorAll("a").forEach(a => a.addEventListener("click", closeMenu));

    document.addEventListener("keydown", e => {
        if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
            e.preventDefault(); search?.focus();
        }
        if (e.key === "Escape") closeMenu();
    });

    search?.addEventListener("input", e => {
        const term = e.target.value.trim().toLowerCase();
        document.dispatchEvent(new CustomEvent("sigem:search", { detail: term }));
    });

    sync?.addEventListener("click", async () => {
        const icon = sync.querySelector("i");
        const original = sync.innerHTML;
        sync.disabled = true;
        sync.classList.add("is-loading");
        sync.innerHTML = '<i class="bi bi-arrow-repeat"></i><span>Sincronizando...</span>';
        try {
            const response = await fetch("/api/sync/run", { method: "POST", headers: {"Accept":"application/json"} });
            const data = await response.json();
            if (!response.ok || !data.success) throw new Error(data.message || "Falha na sincronização");
            showToast("Excel sincronizado com sucesso.", "success");
            window.dispatchEvent(new CustomEvent("sigem:sync-complete", {detail:data}));
        } catch (error) {
            showToast(error.message || "Não foi possível sincronizar.", "danger");
        } finally {
            sync.disabled = false;
            sync.classList.remove("is-loading");
            sync.innerHTML = original;
        }
    });

    window.showToast = function(message, type="info") {
        const region = document.getElementById("toastRegion");
        if (!region) return;
        const el = document.createElement("div");
        el.className = `sigem-toast ${type}`;
        el.innerHTML = `<i class="bi ${type === "success" ? "bi-check-circle-fill" : type === "danger" ? "bi-exclamation-octagon-fill" : "bi-info-circle-fill"}"></i><span>${message}</span>`;
        region.appendChild(el);
        requestAnimationFrame(() => el.classList.add("show"));
        setTimeout(() => { el.classList.remove("show"); setTimeout(() => el.remove(), 250); }, 3800);
    };
});
