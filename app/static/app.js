(() => {
  const STORAGE_KEY = "smartmeal.planConfig.v1";
  const form = document.querySelector("form.grid-form");
  const familySizeInput = document.getElementById("family_size");
  const totalEl = document.getElementById("composition-total");
  const budgetMinInput = document.getElementById("budget_min");
  const budgetMaxInput = document.getElementById("budget_max");
  const weekStartInput = document.getElementById("week_start");
  const offerModeInput = document.getElementById("offer_mode");
  const regionInput = document.getElementById("region");
  const saveConfigButton = document.getElementById("save-config");
  const loadConfigButton = document.getElementById("load-config");
  const resetConfigButton = document.getElementById("reset-config");
  const configStatus = document.getElementById("config-status");
  const storeInputs = Array.from(document.querySelectorAll('input[name="stores"]'));
  const presetButtons = Array.from(document.querySelectorAll(".preset-btn"));
  const compositionInputs = ["babies", "toddlers", "children", "teenagers", "adults"]
    .map((id) => document.getElementById(id))
    .filter(Boolean);
  const compositionById = Object.fromEntries(compositionInputs.map((input) => [input.id, input]));

  let updateCompositionTotal = null;
  if (familySizeInput && totalEl && compositionInputs.length) {
    updateCompositionTotal = () => {
      const total = compositionInputs.reduce((sum, input) => {
        const n = Number.parseInt(input.value || "0", 10);
        return sum + (Number.isFinite(n) ? Math.max(0, n) : 0);
      }, 0);
      totalEl.textContent = String(total);
      if (total > 0) {
        familySizeInput.value = String(total);
      }
    };

    compositionInputs.forEach((input) => {
      input.addEventListener("input", updateCompositionTotal);
    });
    updateCompositionTotal();
  }

  if (presetButtons.length && compositionInputs.length && updateCompositionTotal) {
    const fieldIds = ["adults", "teenagers", "children", "toddlers", "babies"];
    const activateButton = (active) => {
      presetButtons.forEach((btn) => {
        btn.classList.toggle("is-active", btn === active);
        btn.setAttribute("aria-pressed", btn === active ? "true" : "false");
      });
    };

    presetButtons.forEach((button) => {
      button.setAttribute("aria-pressed", "false");
      button.addEventListener("click", () => {
        fieldIds.forEach((id) => {
          const input = compositionById[id];
          if (!input) {
            return;
          }
          const value = Number.parseInt(button.dataset[id] || "0", 10);
          input.value = Number.isFinite(value) ? String(Math.max(0, value)) : "0";
        });
        updateCompositionTotal();
        activateButton(button);
      });
    });
  }

  const clearPresetSelection = () => {
    presetButtons.forEach((btn) => {
      btn.classList.remove("is-active");
      btn.setAttribute("aria-pressed", "false");
    });
  };

  const setStatus = (text) => {
    if (!configStatus) {
      return;
    }
    configStatus.textContent = text;
  };

  const serializeConfig = () => ({
    family_size: familySizeInput?.value || "",
    budget_min: budgetMinInput?.value || "",
    budget_max: budgetMaxInput?.value || "",
    week_start: weekStartInput?.value || "",
    offer_mode: offerModeInput?.value || "",
    region: regionInput?.value || "",
    babies: compositionById.babies?.value || "0",
    toddlers: compositionById.toddlers?.value || "0",
    children: compositionById.children?.value || "0",
    teenagers: compositionById.teenagers?.value || "0",
    adults: compositionById.adults?.value || "0",
    stores: storeInputs.filter((item) => item.checked).map((item) => item.value),
    saved_at: Date.now(),
  });

  const applyConfig = (config) => {
    if (!config || typeof config !== "object") {
      return;
    }

    if (familySizeInput && typeof config.family_size === "string") {
      familySizeInput.value = config.family_size;
    }
    if (budgetMinInput && typeof config.budget_min === "string") {
      budgetMinInput.value = config.budget_min;
    }
    if (budgetMaxInput && typeof config.budget_max === "string") {
      budgetMaxInput.value = config.budget_max;
    }
    if (weekStartInput && typeof config.week_start === "string") {
      weekStartInput.value = config.week_start;
    }
    if (offerModeInput && typeof config.offer_mode === "string") {
      offerModeInput.value = config.offer_mode;
    }
    if (regionInput && typeof config.region === "string") {
      regionInput.value = config.region;
    }

    ["babies", "toddlers", "children", "teenagers", "adults"].forEach((id) => {
      const input = compositionById[id];
      const value = config[id];
      if (input && typeof value === "string") {
        input.value = value;
      }
    });

    if (Array.isArray(config.stores) && storeInputs.length) {
      const selected = new Set(config.stores);
      storeInputs.forEach((item) => {
        item.checked = selected.has(item.value);
      });
    }

    if (updateCompositionTotal) {
      updateCompositionTotal();
    }
    clearPresetSelection();
  };

  if (saveConfigButton && loadConfigButton && resetConfigButton) {
    saveConfigButton.addEventListener("click", () => {
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(serializeConfig()));
        setStatus("Auswahl lokal gespeichert.");
      } catch (_err) {
        setStatus("Speichern fehlgeschlagen.");
      }
    });

    loadConfigButton.addEventListener("click", () => {
      try {
        const raw = window.localStorage.getItem(STORAGE_KEY);
        if (!raw) {
          setStatus("Noch keine gespeicherte Auswahl vorhanden.");
          return;
        }
        const parsed = JSON.parse(raw);
        applyConfig(parsed);
        setStatus("Gespeicherte Auswahl geladen.");
      } catch (_err) {
        setStatus("Laden fehlgeschlagen.");
      }
    });

    resetConfigButton.addEventListener("click", () => {
      window.localStorage.removeItem(STORAGE_KEY);
      setStatus("Gespeicherte Auswahl geloescht.");
    });
  }

  if (form) {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        applyConfig(parsed);
        setStatus("Letzte gespeicherte Auswahl automatisch geladen.");
      }
    } catch (_err) {
      setStatus("Automatisches Laden war nicht moeglich.");
    }
  }

  const copyButton = document.getElementById("copy-markdown");
  const markdown = document.getElementById("markdown-output");
  if (copyButton && markdown) {
    const originalLabel = copyButton.textContent || "Markdown kopieren";

    copyButton.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(markdown.value);
        copyButton.textContent = "Kopiert";
        copyButton.disabled = true;
        window.setTimeout(() => {
          copyButton.textContent = originalLabel;
          copyButton.disabled = false;
        }, 1200);
      } catch (_err) {
        copyButton.textContent = "Kopieren fehlgeschlagen";
        window.setTimeout(() => {
          copyButton.textContent = originalLabel;
        }, 1800);
      }
    });
  }
})();
