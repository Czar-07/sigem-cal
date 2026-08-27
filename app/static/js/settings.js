/* ============================================================
   SIGEM CAL
   SETTINGS.JS
   Página de Configurações
   Versão integrada com API real
   ============================================================ */

"use strict";


/* ============================================================
   1. CONFIGURAÇÃO
   ============================================================ */

const Settings = (() => {

    const CONFIG = {

        API: {
            settings:
                "/api/settings",

            bulk:
                "/api/settings/bulk",

            resetAll:
                "/api/settings/reset-all",

            initialize:
                "/api/settings/initialize",

            categories:
                "/api/settings/meta/categories"
        },


        SELECTORS: {

            page:
                ".settings-page",

            form:
                "#settingsForm",

            saveButton:
                "#saveSettings",

            resetButton:
                "#resetSettings",

            restoreButton:
                "#restoreDefaults",

            loading:
                "#settingsLoading",

            content:
                "#settingsContent",

            toastContainer:
                "#settingsToastContainer",

            navItems:
                ".settings-nav-item",

            sections:
                ".settings-section",

            /*
             * CAMPOS DO HTML REAL
             */

            systemName:
                "#systemName",

            systemDescription:
                "#systemDescription",

            systemLanguage:
                "#systemLanguage",

            systemTimezone:
                "#systemTimezone",

            companyName:
                "#companyName",

            theme:
                "#theme",

            sidebarCollapsed:
                "#sidebarCollapsed",

            animations:
                "#animations",

            notificationsEnabled:
                "#notificationsEnabled",

            notificationsCalibration:
                "#notificationsCalibration",

            notificationsExpirationDays:
                "#notificationsExpirationDays",

            calibrationAlertDays:
                "#calibrationAlertDays",

            calibrationOverdueEnabled:
                "#calibrationOverdueEnabled",

            refreshEnabled:
                "#refreshEnabled",

            refreshInterval:
                "#refreshInterval",

            /*
             * ELEMENTOS DE BANCO
             */

            databaseStatus:
                "#databaseStatus",

            databaseDevices:
                "#databaseDevices",

            databaseCertificates:
                "#databaseCertificates",

            databaseSettings:
                "#databaseSettings"

        },


        /*
         * VALORES PADRÃO
         *
         * Devem refletir DEFAULT_SETTINGS
         * do backend.
         */

        DEFAULTS: {

            "system.name":
                "SIGEM CAL",

            "system.description":
                "Sistema Inteligente de Gestão de Calibração",

            "system.language":
                "pt-BR",

            "system.timezone":
                "America/Sao_Paulo",

            "appearance.theme":
                "light",

            "appearance.sidebar_collapsed":
                false,

            "appearance.animations":
                true,

            "notifications.enabled":
                true,

            "notifications.calibration":
                true,

            "notifications.expiration_days":
                30,

            "calibration.alert_days":
                30,

            "calibration.overdue_enabled":
                true,

            "system.refresh_enabled":
                true,

            "system.refresh_interval":
                60

        }

    };


    /* ========================================================
       2. ESTADO
       ======================================================== */

    const state = {

        settings:
            {},

        originalSettings:
            {},

        metadata:
            {},

        loading:
            false,

        saving:
            false,

        dirty:
            false,

        initialized:
            false

    };


    /* ========================================================
       3. INICIALIZAÇÃO
       ======================================================== */

    function init() {

        const page =
            document.querySelector(
                CONFIG.SELECTORS.page
            );


        if (!page) {
            return;
        }


        if (state.initialized) {
            return;
        }


        state.initialized =
            true;


        bindEvents();

        setupNavigation();

        setupHashNavigation();

        loadSettings();
        loadDatabaseStatus();

    }


    /* ========================================================
       4. EVENTOS
       ======================================================== */

    function bindEvents() {

        const form =
            document.querySelector(
                CONFIG.SELECTORS.form
            );


        if (form) {

            form.addEventListener(
                "input",
                handleFormChange
            );


            form.addEventListener(
                "change",
                handleFormChange
            );


            form.addEventListener(
                "submit",
                handleSubmit
            );

        }


        bindClick(
            CONFIG.SELECTORS.saveButton,
            saveSettings
        );


        bindClick(
            CONFIG.SELECTORS.resetButton,
            resetChanges
        );


        bindClick(
            CONFIG.SELECTORS.restoreButton,
            restoreDefaults
        );

        bindClick(
            "#testEmailButton",
            testEmail
        );


        bindChange(
            CONFIG.SELECTORS.theme,
            handleThemeChange
        );


        bindChange(
            CONFIG.SELECTORS.refreshEnabled,
            updateConditionalFields
        );


        bindChange(
            CONFIG.SELECTORS.notificationsEnabled,
            updateConditionalFields
        );


        bindChange(
            CONFIG.SELECTORS.notificationsCalibration,
            updateConditionalFields
        );


        bindChange(
            CONFIG.SELECTORS.calibrationOverdueEnabled,
            updateConditionalFields
        );


        window.addEventListener(
            "beforeunload",
            handleBeforeUnload
        );

    }


    /* ========================================================
       5. NAVEGAÇÃO
       ======================================================== */

    function setupNavigation() {

        const items =
            document.querySelectorAll(
                CONFIG.SELECTORS.navItems
            );


        const sections =
            document.querySelectorAll(
                CONFIG.SELECTORS.sections
            );


        if (!items.length) {
            return;
        }


        items.forEach(item => {

            item.addEventListener(
                "click",
                event => {

                    event.preventDefault();


                    const target =
                        item.dataset.settingsSection;


                    if (!target) {
                        return;
                    }


                    activateSection(
                        target,
                        true
                    );

                }
            );

        });


        observeSections(
            sections,
            items
        );

    }


    /* ========================================================
       6. HASH
       ======================================================== */

    function setupHashNavigation() {

        const hash =
            window.location.hash
                .replace("#", "")
                .trim();


        if (!hash) {
            return;
        }


        const section =
            document.querySelector(
                `[data-settings-content="${hash}"]`
            );


        if (!section) {
            return;
        }


        setTimeout(
            () => activateSection(
                hash,
                false
            ),
            50
        );

    }


    /* ========================================================
       7. ATIVAR SEÇÃO
       ======================================================== */

    function activateSection(
        target,
        updateHash = true
    ) {

        const sections =
            document.querySelectorAll(
                CONFIG.SELECTORS.sections
            );


        const items =
            document.querySelectorAll(
                CONFIG.SELECTORS.navItems
            );


        const section =
            document.querySelector(
                `[data-settings-content="${target}"]`
            );


        if (!section) {
            return;
        }


        sections.forEach(
            item =>
                item.classList.toggle(
                    "active",
                    item.dataset.settingsContent ===
                    target
                )
        );


        items.forEach(
            item =>
                item.classList.toggle(
                    "active",
                    item.dataset.settingsSection ===
                    target
                )
        );


        if (updateHash) {

            history.replaceState(
                null,
                "",
                `#${target}`
            );

        }


        section.scrollIntoView({

            behavior:
                "smooth",

            block:
                "start"

        });

    }


    /* ========================================================
       8. INTERSECTION OBSERVER
       ======================================================== */

    function observeSections(
        sections,
        items
    ) {

        if (
            !sections.length ||
            !("IntersectionObserver" in window)
        ) {
            return;
        }


        const observer =
            new IntersectionObserver(

                entries => {

                    const visible =
                        entries
                            .filter(
                                entry =>
                                    entry.isIntersecting
                            )
                            .sort(
                                (a, b) =>
                                    b.intersectionRatio -
                                    a.intersectionRatio
                            )[0];


                    if (!visible) {
                        return;
                    }


                    const id =
                        visible.target
                            .dataset
                            .settingsContent;


                    items.forEach(item => {

                        item.classList.toggle(

                            "active",

                            item.dataset.settingsSection ===
                            id

                        );

                    });

                },

                {

                    root:
                        null,

                    rootMargin:
                        "-15% 0px -70% 0px",

                    threshold: [
                        0.05,
                        0.25,
                        0.5
                    ]

                }

            );


        sections.forEach(
            section =>
                observer.observe(
                    section
                )
        );

    }


    /* ========================================================
       9. CARREGAR CONFIGURAÇÕES
       ======================================================== */

    async function loadSettings() {

        setLoading(true);


        try {

            const response =
                await fetch(
                    CONFIG.API.settings,
                    {

                        method:
                            "GET",

                        headers: {

                            "Accept":
                                "application/json"

                        },

                        credentials:
                            "same-origin"

                    }
                );


            const data =
                await parseResponse(
                    response
                );


            if (
                !response.ok ||
                data.success === false
            ) {

                throw new Error(
                    data.message ||
                    `Erro HTTP ${response.status}`
                );

            }


            /*
             * A API REAL retorna:
             *
             * data.configuracoes
             *
             * e não data.settings.
             */

            state.metadata =
                Array.isArray(
                    data.configuracoes
                )
                    ? data.configuracoes
                    : [];


            state.settings =
                convertApiSettings(
                    state.metadata
                );


            state.originalSettings =
                clone(
                    state.settings
                );


            populateForm(
                state.settings
            );


            setDirty(false);

            updateConditionalFields();

            applyTheme(
                state.settings[
                    "appearance.theme"
                ]
            );


            showToast(
                "Configurações carregadas.",
                "success"
            );


        } catch (error) {

            console.error(
                "SIGEM CAL — Erro ao carregar configurações:",
                error
            );


            /*
             * Não sobrescrevemos silenciosamente
             * o banco com defaults.
             *
             * Os defaults são usados somente
             * para permitir a interface iniciar.
             */

            state.settings =
                clone(
                    CONFIG.DEFAULTS
                );


            state.originalSettings =
                clone(
                    state.settings
                );


            populateForm(
                state.settings
            );


            updateConditionalFields();


            showToast(
                "Não foi possível carregar as configurações do servidor. Os valores padrão foram exibidos.",
                "warning"
            );


        } finally {

            setLoading(false);

        }

    }


    /* ========================================================
       10. CONVERTER RESPOSTA DA API
       ======================================================== */

    function convertApiSettings(
        configuracoes
    ) {

        const settings =
            clone(
                CONFIG.DEFAULTS
            );


        if (!Array.isArray(configuracoes)) {
            return settings;
        }


        configuracoes.forEach(
            item => {

                if (
                    !item ||
                    !item.chave
                ) {
                    return;
                }


                settings[
                    item.chave
                ] =
                    normalizeValue(
                        item.valor,
                        item.tipo
                    );

            }
        );


        return settings;

    }


    /* ========================================================
       11. NORMALIZAR VALOR
       ======================================================== */

    function normalizeValue(
        value,
        type
    ) {

        if (
            type ===
            "integer"
        ) {

            const number =
                Number(value);


            return Number.isFinite(
                number
            )
                ? Math.trunc(number)
                : 0;

        }


        if (
            type ===
            "float"
        ) {

            const number =
                Number(value);


            return Number.isFinite(
                number
            )
                ? number
                : 0;

        }


        if (
            type ===
            "boolean"
        ) {

            return toBoolean(
                value
            );

        }


        return value ??
            "";

    }


    /* ========================================================
       12. PREENCHER FORMULÁRIO
       ======================================================== */

    function populateForm(
        settings
    ) {

        /*
         * Campos que possuem data-setting.
         */

        const fields =
            document.querySelectorAll(
                "[data-setting]"
            );


        fields.forEach(
            field => {

                const key =
                    field.dataset.setting;


                if (!key) {
                    return;
                }


                if (
                    !Object.prototype.hasOwnProperty.call(
                        settings,
                        key
                    )
                ) {
                    return;
                }


                setFieldValue(
                    field,
                    settings[key]
                );

            }
        );


        /*
         * Compatibilidade com o HTML atual.
         */

        setValue(
            CONFIG.SELECTORS.systemName,
            settings[
                "system.name"
            ]
        );


        setValue(
            CONFIG.SELECTORS.systemDescription,
            settings[
                "system.description"
            ]
        );


        setValue(
            CONFIG.SELECTORS.systemLanguage,
            settings[
                "system.language"
            ]
        );


        setValue(
            CONFIG.SELECTORS.systemTimezone,
            settings[
                "system.timezone"
            ]
        );


        setValue(
            CONFIG.SELECTORS.companyName,
            settings[
                "company.name"
            ] ??
            settings.companyName ??
            ""
        );


        setValue(
            CONFIG.SELECTORS.theme,
            settings[
                "appearance.theme"
            ]
        );


        setChecked(
            CONFIG.SELECTORS.sidebarCollapsed,
            settings[
                "appearance.sidebar_collapsed"
            ]
        );


        setChecked(
            CONFIG.SELECTORS.animations,
            settings[
                "appearance.animations"
            ]
        );


        setChecked(
            CONFIG.SELECTORS.notificationsEnabled,
            settings[
                "notifications.enabled"
            ]
        );


        setChecked(
            CONFIG.SELECTORS.notificationsCalibration,
            settings[
                "notifications.calibration"
            ]
        );


        setValue(
            CONFIG.SELECTORS.notificationsExpirationDays,
            settings[
                "notifications.expiration_days"
            ]
        );


        setValue(
            CONFIG.SELECTORS.calibrationAlertDays,
            settings[
                "calibration.alert_days"
            ]
        );


        setChecked(
            CONFIG.SELECTORS.calibrationOverdueEnabled,
            settings[
                "calibration.overdue_enabled"
            ]
        );


        setChecked(
            CONFIG.SELECTORS.refreshEnabled,
            settings[
                "system.refresh_enabled"
            ]
        );


        setValue(
            CONFIG.SELECTORS.refreshInterval,
            settings[
                "system.refresh_interval"
            ]
        );

    }


    /* ========================================================
       13. CAPTURAR FORMULÁRIO
       ======================================================== */

    function collectForm() {

        const settings =
            clone(
                state.settings
            );


        /*
         * Primeiro coletamos todos os
         * data-setting.
         */

        const fields =
            document.querySelectorAll(
                "[data-setting]"
            );


        fields.forEach(
            field => {

                const key =
                    field.dataset.setting;


                if (!key) {
                    return;
                }


                settings[key] =
                    getFieldValue(
                        field
                    );

            }
        );


        /*
         * Mapeamento explícito para o HTML
         * atual.
         */

        collectId(
            settings,
            "system.name",
            CONFIG.SELECTORS.systemName
        );


        collectId(
            settings,
            "system.description",
            CONFIG.SELECTORS.systemDescription
        );


        collectId(
            settings,
            "system.language",
            CONFIG.SELECTORS.systemLanguage
        );


        collectId(
            settings,
            "system.timezone",
            CONFIG.SELECTORS.systemTimezone
        );


        collectId(
            settings,
            "company.name",
            CONFIG.SELECTORS.companyName
        );


        collectId(
            settings,
            "appearance.theme",
            CONFIG.SELECTORS.theme
        );


        collectId(
            settings,
            "appearance.sidebar_collapsed",
            CONFIG.SELECTORS.sidebarCollapsed
        );


        collectId(
            settings,
            "appearance.animations",
            CONFIG.SELECTORS.animations
        );


        collectId(
            settings,
            "notifications.enabled",
            CONFIG.SELECTORS.notificationsEnabled
        );


        collectId(
            settings,
            "notifications.calibration",
            CONFIG.SELECTORS.notificationsCalibration
        );


        collectId(
            settings,
            "notifications.expiration_days",
            CONFIG.SELECTORS.notificationsExpirationDays
        );


        collectId(
            settings,
            "calibration.alert_days",
            CONFIG.SELECTORS.calibrationAlertDays
        );


        collectId(
            settings,
            "calibration.overdue_enabled",
            CONFIG.SELECTORS.calibrationOverdueEnabled
        );


        collectId(
            settings,
            "system.refresh_enabled",
            CONFIG.SELECTORS.refreshEnabled
        );


        collectId(
            settings,
            "system.refresh_interval",
            CONFIG.SELECTORS.refreshInterval
        );


        return normalizeCollectedSettings(
            settings
        );

    }


    /* ========================================================
       14. NORMALIZAR FORMULÁRIO
       ======================================================== */

    function normalizeCollectedSettings(
        settings
    ) {

        const result =
            clone(
                settings
            );


        result[
            "system.name"
        ] =
            String(
                result[
                    "system.name"
                ] ??
                ""
            ).trim();


        result[
            "system.description"
        ] =
            String(
                result[
                    "system.description"
                ] ??
                ""
            ).trim();


        result[
            "system.language"
        ] =
            String(
                result[
                    "system.language"
                ] ??
                "pt-BR"
            );


        result[
            "system.timezone"
        ] =
            String(
                result[
                    "system.timezone"
                ] ??
                "America/Sao_Paulo"
            );


        result[
            "appearance.theme"
        ] =
            String(
                result[
                    "appearance.theme"
                ] ??
                "light"
            );


        result[
            "appearance.sidebar_collapsed"
        ] =
            toBoolean(
                result[
                    "appearance.sidebar_collapsed"
                ]
            );


        result[
            "appearance.animations"
        ] =
            toBoolean(
                result[
                    "appearance.animations"
                ]
            );


        result[
            "notifications.enabled"
        ] =
            toBoolean(
                result[
                    "notifications.enabled"
                ]
            );


        result[
            "notifications.calibration"
        ] =
            toBoolean(
                result[
                    "notifications.calibration"
                ]
            );


        result[
            "notifications.expiration_days"
        ] =
            integerOrDefault(
                result[
                    "notifications.expiration_days"
                ],
                30
            );


        result[
            "calibration.alert_days"
        ] =
            integerOrDefault(
                result[
                    "calibration.alert_days"
                ],
                30
            );


        result[
            "calibration.overdue_enabled"
        ] =
            toBoolean(
                result[
                    "calibration.overdue_enabled"
                ]
            );


        result[
            "system.refresh_enabled"
        ] =
            toBoolean(
                result[
                    "system.refresh_enabled"
                ]
            );


        result[
            "system.refresh_interval"
        ] =
            integerOrDefault(
                result[
                    "system.refresh_interval"
                ],
                60
            );


        return result;

    }


    /* ========================================================
       15. SALVAR
       ======================================================== */

    async function saveSettings() {

        if (state.saving) {
            return;
        }


        const settings =
            collectForm();


        const validation =
            validateSettings(
                settings
            );


        if (!validation.valid) {

            showToast(
                validation.message,
                "danger"
            );

            return;

        }


        /*
         * Só enviamos configurações existentes
         * no backend.
         */

        const payload =
            buildBulkPayload(
                settings
            );


        if (
            Object.keys(
                payload
            ).length === 0
        ) {

            showToast(
                "Nenhuma configuração válida para salvar.",
                "warning"
            );

            return;

        }


        setSaving(true);


        try {

            const response =
                await fetch(
                    CONFIG.API.bulk,
                    {

                        method:
                            "PUT",

                        headers: {

                            "Content-Type":
                                "application/json",

                            "Accept":
                                "application/json"

                        },

                        credentials:
                            "same-origin",

                        body:
                            JSON.stringify({

                                configuracoes:
                                    payload

                            })

                    }
                );


            const data =
                await parseResponse(
                    response
                );


            if (
                !response.ok ||
                data.success === false
            ) {

                throw new Error(
                    data.message ||
                    `Erro HTTP ${response.status}`
                );

            }


            /*
             * Atualiza o estado com os valores
             * efetivamente salvos.
             */

            if (
                Array.isArray(
                    data.configuracoes
                )
            ) {

                data.configuracoes.forEach(
                    item => {

                        if (!item?.chave) {
                            return;
                        }


                        state.settings[
                            item.chave
                        ] =
                            normalizeValue(
                                item.valor,
                                item.tipo
                            );

                    }
                );

            } else {

                Object.assign(
                    state.settings,
                    payload
                );

            }


            state.originalSettings =
                clone(
                    state.settings
                );


            populateForm(
                state.settings
            );


            setDirty(false);

            updateConditionalFields();


            applyTheme(
                state.settings[
                    "appearance.theme"
                ]
            );


            showToast(
                data.message ||
                "Configurações salvas com sucesso.",
                "success"
            );


        } catch (error) {

            console.error(
                "SIGEM CAL — Erro ao salvar:",
                error
            );


            showToast(
                error.message ||
                "Não foi possível salvar as configurações.",
                "danger"
            );


        } finally {

            setSaving(false);

        }

    }


    /* ========================================================
       16. MONTAR PAYLOAD BULK
       ======================================================== */

    function buildBulkPayload(
        settings
    ) {

        const payload =
            {};


        /*
         * Somente chaves realmente existentes
         * no backend.
         */

        const knownKeys =
            new Set(

                Object.keys(
                    CONFIG.DEFAULTS
                )

            );


        Object.entries(
            settings
        ).forEach(
            ([key, value]) => {

                if (
                    !knownKeys.has(
                        key
                    )
                ) {
                    return;
                }


                payload[key] =
                    value;

            }
        );


        return payload;

    }


    /* ========================================================
       17. RESTAURAR TODAS
       ======================================================== */

    async function restoreDefaults() {

        const confirmed =
            window.confirm(
                "Deseja restaurar todas as configurações para os valores padrão?"
            );


        if (!confirmed) {
            return;
        }


        setSaving(true);


        try {

            const response =
                await fetch(
                    CONFIG.API.resetAll,
                    {

                        method:
                            "POST",

                        headers: {

                            "Accept":
                                "application/json"

                        },

                        credentials:
                            "same-origin"

                    }
                );


            const data =
                await parseResponse(
                    response
                );


            if (
                !response.ok ||
                data.success === false
            ) {

                throw new Error(
                    data.message ||
                    `Erro HTTP ${response.status}`
                );

            }


            /*
             * Após restaurar no servidor,
             * carregamos novamente.
             */

            await loadSettings();


            showToast(
                data.message ||
                "Configurações restauradas com sucesso.",
                "success"
            );


        } catch (error) {

            console.error(
                "SIGEM CAL — Erro ao restaurar padrões:",
                error
            );


            showToast(
                error.message ||
                "Não foi possível restaurar as configurações.",
                "danger"
            );


        } finally {

            setSaving(false);

        }

    }


    /* ========================================================
       18. DESCARTAR ALTERAÇÕES
       ======================================================== */

    function resetChanges() {

        if (!state.dirty) {

            showToast(
                "Não existem alterações pendentes.",
                "info"
            );

            return;

        }


        const confirmed =
            window.confirm(
                "Deseja descartar todas as alterações realizadas?"
            );


        if (!confirmed) {
            return;
        }


        state.settings =
            clone(
                state.originalSettings
            );


        populateForm(
            state.settings
        );


        updateConditionalFields();


        applyTheme(
            state.settings[
                "appearance.theme"
            ]
        );


        setDirty(false);


        showToast(
            "Alterações descartadas.",
            "info"
        );

    }


    /* ========================================================
       19. ALTERAÇÃO DO FORMULÁRIO
       ======================================================== */

    function handleFormChange() {

        const current =
            collectForm();


        const changed =
            !objectsEqual(
                current,
                state.originalSettings
            );


        setDirty(
            changed
        );


        updateConditionalFields();

    }


    /* ========================================================
       20. SUBMIT
       ======================================================== */

    function handleSubmit(
        event
    ) {

        event.preventDefault();

        saveSettings();

    }


    /* ========================================================
       21. TEMA
       ======================================================== */

    function handleThemeChange(
        event
    ) {

        applyTheme(
            event.target.value
        );


        handleFormChange();

    }


    function applyTheme(
        theme
    ) {

        const normalized =
            String(
                theme ||
                "light"
            ).toLowerCase();


        if (
            normalized ===
            "system"
        ) {

            document.documentElement
                .removeAttribute(
                    "data-theme"
                );

            return;

        }


        document.documentElement
            .setAttribute(
                "data-theme",
                normalized
            );

    }


    /* ========================================================
       22. CAMPOS CONDICIONAIS
       ======================================================== */

    function updateConditionalFields() {

        /*
         * Atualização automática
         */

        const refreshEnabled =
            getChecked(
                CONFIG.SELECTORS.refreshEnabled
            );


        toggleField(
            CONFIG.SELECTORS.refreshInterval,
            refreshEnabled
        );


        /*
         * Notificações
         */

        const notificationsEnabled =
            getChecked(
                CONFIG.SELECTORS.notificationsEnabled
            );


        toggleField(
            CONFIG.SELECTORS.notificationsCalibration,
            notificationsEnabled
        );


        toggleField(
            CONFIG.SELECTORS.notificationsExpirationDays,
            notificationsEnabled
        );


        /*
         * Calibração
         */

        const calibrationEnabled =
            getChecked(
                CONFIG.SELECTORS.notificationsCalibration
            );


        toggleField(
            CONFIG.SELECTORS.calibrationAlertDays,
            calibrationEnabled
        );

    }


    function toggleField(
        selector,
        enabled
    ) {

        const field =
            document.querySelector(
                selector
            );


        if (!field) {
            return;
        }


        field.disabled =
            !enabled;


        const wrapper =
            field.closest(
                ".settings-field, .setting-item, .form-group"
            );


        if (wrapper) {

            wrapper.classList.toggle(
                "is-disabled",
                !enabled
            );

        }

    }


    /* ========================================================
       23. VALIDAÇÃO
       ======================================================== */

    function validateSettings(
        settings
    ) {

        const name =
            settings[
                "system.name"
            ];


        if (
            !name ||
            name.length < 2
        ) {

            return {

                valid:
                    false,

                message:
                    "Informe um nome válido para o sistema."

            };

        }


        const expirationDays =
            Number(
                settings[
                    "notifications.expiration_days"
                ]
            );


        if (
            !Number.isInteger(
                expirationDays
            ) ||
            expirationDays < 1 ||
            expirationDays > 365
        ) {

            return {

                valid:
                    false,

                message:
                    "Os dias de antecedência da notificação devem estar entre 1 e 365."

            };

        }


        const alertDays =
            Number(
                settings[
                    "calibration.alert_days"
                ]
            );


        if (
            !Number.isInteger(
                alertDays
            ) ||
            alertDays < 1 ||
            alertDays > 365
        ) {

            return {

                valid:
                    false,

                message:
                    "Os dias de antecedência da calibração devem estar entre 1 e 365."

            };

        }


        const refreshInterval =
            Number(
                settings[
                    "system.refresh_interval"
                ]
            );


        if (
            !Number.isInteger(
                refreshInterval
            ) ||
            refreshInterval < 10 ||
            refreshInterval > 3600
        ) {

            return {

                valid:
                    false,

                message:
                    "O intervalo de atualização deve estar entre 10 e 3600 segundos."

            };

        }


        return {

            valid:
                true

        };

    }


    async function testEmail() {
        const button = document.querySelector("#testEmailButton");
        if (button) { button.disabled = true; button.dataset.original = button.innerHTML; button.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Enviando...'; }
        try {
            const response = await fetch("/api/notifications/test-email", { method: "POST", headers: {"Accept":"application/json"} });
            const data = await parseResponse(response);
            if (!response.ok || !data.success) throw new Error(data.message || "Falha ao enviar o e-mail.");
            showToast(data.message, "success");
        } catch (error) {
            showToast(error.message, "danger");
        } finally {
            if (button) { button.disabled = false; button.innerHTML = button.dataset.original || "Enviar e-mail de teste"; }
        }
    }

    async function loadDatabaseStatus() {
        try {
            const response = await fetch("/api/dashboard", { cache: "no-store" });
            const data = await parseResponse(response);
            if (!response.ok || !data.success) throw new Error("Falha");
            setValue(CONFIG.SELECTORS.databaseDevices, data.total ?? 0);
            setValue(CONFIG.SELECTORS.databaseCertificates, data.certificados ? (data.certificados["2025"] + data.certificados["2026"]) : "—");
            const sync = data.sync?.updated_at;
            const syncEl = document.getElementById("databaseSync");
            if (syncEl) syncEl.textContent = sync ? new Date(sync).toLocaleString("pt-BR") : "—";
            const status = document.getElementById("databaseStatus");
            if (status) status.textContent = "Conectado";
        } catch (error) {
            const status = document.getElementById("databaseStatus");
            if (status) status.textContent = "Indisponível";
        }
    }

    /* ========================================================
       24. LOADING
       ======================================================== */

    function setLoading(
        loading
    ) {

        state.loading =
            loading;


        const loadingElement =
            document.querySelector(
                CONFIG.SELECTORS.loading
            );


        const content =
            document.querySelector(
                CONFIG.SELECTORS.content
            );


        if (loadingElement) {

            loadingElement.classList.toggle(
                "d-none",
                !loading
            );

        }


        if (content) {

            content.classList.toggle(
                "is-loading",
                loading
            );

        }

    }


    /* ========================================================
       25. SAVING
       ======================================================== */

    function setSaving(
        saving
    ) {

        state.saving =
            saving;


        const button =
            document.querySelector(
                CONFIG.SELECTORS.saveButton
            );


        if (!button) {
            return;
        }


        button.disabled =
            saving;


        if (saving) {

            if (
                !button.dataset.originalHtml
            ) {

                button.dataset.originalHtml =
                    button.innerHTML;

            }


            button.innerHTML = `

                <span
                    class="spinner-border spinner-border-sm"
                    aria-hidden="true">
                </span>

                Salvando...

            `;

        } else {

            button.innerHTML =
                button.dataset.originalHtml ||
                `

                    <i class="bi bi-check2"></i>

                    Salvar alterações

                `;

        }

    }


    /* ========================================================
       26. DIRTY STATE
       ======================================================== */

    function setDirty(
        dirty
    ) {

        state.dirty =
            Boolean(
                dirty
            );


        const page =
            document.querySelector(
                CONFIG.SELECTORS.page
            );


        if (page) {

            page.classList.toggle(
                "has-unsaved-changes",
                state.dirty
            );

        }


        const button =
            document.querySelector(
                CONFIG.SELECTORS.saveButton
            );


        if (button) {

            button.classList.toggle(
                "is-dirty",
                state.dirty
            );

        }


        updateUnsavedIndicator(
            state.dirty
        );

    }


    /* ========================================================
       27. INDICADOR DE ALTERAÇÕES
       ======================================================== */

    function updateUnsavedIndicator(
        dirty
    ) {

        let indicator =
            document.querySelector(
                "#settingsUnsavedIndicator"
            );


        if (!dirty) {

            if (indicator) {
                indicator.remove();
            }

            return;

        }


        if (indicator) {
            return;
        }


        indicator =
            document.createElement(
                "span"
            );


        indicator.id =
            "settingsUnsavedIndicator";


        indicator.className =
            "settings-unsaved-indicator";


        indicator.innerHTML = `

            <i class="bi bi-circle-fill"></i>

            Alterações não salvas

        `;


        const button =
            document.querySelector(
                CONFIG.SELECTORS.saveButton
            );


        if (
            button &&
            button.parentElement
        ) {

            button.parentElement.prepend(
                indicator
            );

        }

    }


    /* ========================================================
       28. BEFORE UNLOAD
       ======================================================== */

    function handleBeforeUnload(
        event
    ) {

        if (!state.dirty) {
            return;
        }


        event.preventDefault();

        event.returnValue = "";

    }


    /* ========================================================
       29. TOAST
       ======================================================== */

    function showToast(
        message,
        type = "info"
    ) {

        let container =
            document.querySelector(
                CONFIG.SELECTORS.toastContainer
            );


        if (!container) {

            container =
                document.createElement(
                    "div"
                );


            container.id =
                "settingsToastContainer";


            container.className =
                "settings-toast-container";


            document.body.appendChild(
                container
            );

        }


        const toast =
            document.createElement(
                "div"
            );


        toast.className =
            `settings-toast settings-toast-${type}`;


        const icons = {

            success:
                "bi-check-circle-fill",

            danger:
                "bi-exclamation-octagon-fill",

            warning:
                "bi-exclamation-triangle-fill",

            info:
                "bi-info-circle-fill"

        };


        const icon =
            icons[type] ||
            icons.info;


        toast.innerHTML = `

            <div class="settings-toast-icon">

                <i class="bi ${icon}"></i>

            </div>

            <div class="settings-toast-content">

                <strong>
                    SIGEM CAL
                </strong>

                <span></span>

            </div>

            <button
                type="button"
                class="settings-toast-close"
                aria-label="Fechar">

                <i class="bi bi-x"></i>

            </button>

        `;


        const messageElement =
            toast.querySelector(
                ".settings-toast-content span"
            );


        if (messageElement) {

            messageElement.textContent =
                message;

        }


        container.appendChild(
            toast
        );


        requestAnimationFrame(
            () => {

                toast.classList.add(
                    "show"
                );

            }
        );


        const close =
            () => {

                toast.classList.remove(
                    "show"
                );


                window.setTimeout(
                    () => {

                        if (
                            toast.isConnected
                        ) {

                            toast.remove();

                        }

                    },
                    200
                );

            };


        const closeButton =
            toast.querySelector(
                ".settings-toast-close"
            );


        if (closeButton) {

            closeButton.addEventListener(
                "click",
                close
            );

        }


        window.setTimeout(
            close,
            4500
        );

    }


    /* ========================================================
       30. HELPERS DOM
       ======================================================== */

    function bindClick(
        selector,
        callback
    ) {

        const element =
            document.querySelector(
                selector
            );


        if (!element) {
            return;
        }


        element.addEventListener(
            "click",
            callback
        );

    }


    function bindChange(
        selector,
        callback
    ) {

        const element =
            document.querySelector(
                selector
            );


        if (!element) {
            return;
        }


        element.addEventListener(
            "change",
            callback
        );

    }


    function setValue(
        selector,
        value
    ) {

        const element =
            document.querySelector(
                selector
            );


        if (!element) {
            return;
        }


        setFieldValue(
            element,
            value
        );

    }


    function setChecked(
        selector,
        value
    ) {

        const element =
            document.querySelector(
                selector
            );


        if (
            !element ||
            element.type !==
            "checkbox"
        ) {
            return;
        }


        element.checked =
            toBoolean(
                value
            );

    }


    function collectId(
        object,
        key,
        selector
    ) {

        const element =
            document.querySelector(
                selector
            );


        if (!element) {
            return;
        }


        object[key] =
            getFieldValue(
                element
            );

    }


    function setFieldValue(
        field,
        value
    ) {

        if (
            field.type ===
            "checkbox"
        ) {

            field.checked =
                toBoolean(
                    value
                );

            return;

        }


        if (
            field.type ===
            "radio"
        ) {

            field.checked =
                String(
                    field.value
                ) ===
                String(
                    value
                );

            return;

        }


        field.value =
            value ??
            "";

    }


    function getFieldValue(
        field
    ) {

        if (
            field.type ===
            "checkbox"
        ) {

            return field.checked;

        }


        if (
            field.type ===
            "number"
        ) {

            const number =
                Number(
                    field.value
                );


            return Number.isFinite(
                number
            )
                ? number
                : 0;

        }


        if (
            field.type ===
            "radio"
        ) {

            return field.checked
                ? field.value
                : null;

        }


        return field.value;

    }


    /* ========================================================
       31. HELPERS DE VALOR
       ======================================================== */

    function getChecked(
        selector
    ) {

        const element =
            document.querySelector(
                selector
            );


        return Boolean(
            element?.checked
        );

    }


    function toBoolean(
        value
    ) {

        if (
            typeof value ===
            "boolean"
        ) {

            return value;

        }


        if (
            typeof value ===
            "number"
        ) {

            return value !== 0;

        }


        if (
            typeof value ===
            "string"
        ) {

            return [

                "true",
                "1",
                "yes",
                "sim",
                "on"

            ].includes(
                value
                    .trim()
                    .toLowerCase()
            );

        }


        return Boolean(
            value
        );

    }


    function integerOrDefault(
        value,
        fallback
    ) {

        const number =
            Number(
                value
            );


        if (
            !Number.isFinite(
                number
            )
        ) {

            return fallback;

        }


        return Math.trunc(
            number
        );

    }


    function clone(
        object
    ) {

        return JSON.parse(
            JSON.stringify(
                object
            )
        );

    }


    function objectsEqual(
        first,
        second
    ) {

        return JSON.stringify(
            first
        ) ===
        JSON.stringify(
            second
        );

    }


    /* ========================================================
       32. RESPONSE API
       ======================================================== */

    async function parseResponse(
        response
    ) {

        const text =
            await response.text();


        if (!text) {
            return {};
        }


        try {

            return JSON.parse(
                text
            );

        } catch {

            throw new Error(
                "O servidor retornou uma resposta inválida."
            );

        }

    }


    /* ========================================================
       33. API PÚBLICA
       ======================================================== */

    return {

        init,

        loadSettings,

        saveSettings,

        resetChanges,

        restoreDefaults,

        getSettings() {

            return clone(
                state.settings
            );

        },

        isDirty() {

            return state.dirty;

        }

    };

})();


/* ============================================================
   34. INICIALIZAÇÃO
   ============================================================ */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        Settings.init();

    }
);