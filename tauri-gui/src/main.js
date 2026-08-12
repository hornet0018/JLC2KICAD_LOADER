const { invoke } = window.__TAURI__.core;
const { listen } = window.__TAURI__.event;
const { open } = window.__TAURI__.dialog;

const DEFAULT_CONFIG = {
  directories: [],
  symbol_lib: "",
  footprint_lib: "footprint",
  symbol_lib_dir: "symbol",
  model_dir: "packages3d",
  model_base_variable: "",
  create_footprint: true,
  create_symbol: true,
  models: "STEP",
  skip_existing: false,
  add_to_all: false,
};

let config = { ...DEFAULT_CONFIG };
let isRunning = false;
let logEl;

function $(id) {
  return document.getElementById(id);
}

function logMessage(message) {
  if (!logEl) return;
  const line = document.createTextNode(message + "\n");
  logEl.appendChild(line);
  logEl.scrollTop = logEl.scrollHeight;
}

function clearLog() {
  if (logEl) logEl.textContent = "";
}

function setStatus(text) {
  $("status").textContent = text;
}

function setRunning(running) {
  isRunning = running;
  $("add-btn").disabled = running;
  const bar = $("progress-bar");
  if (running) {
    bar.classList.add("indeterminate");
  } else {
    bar.classList.remove("indeterminate");
    bar.style.width = "0%";
  }
}

function getConfigFromUI() {
  const dirList = $("dir-list");
  const directories = Array.from(dirList.options).map((opt) => opt.value);
  return {
    directories,
    symbol_lib: $("symbol-lib").value.trim(),
    footprint_lib: $("footprint-lib").value.trim() || "footprint",
    symbol_lib_dir: $("symbol-lib-dir").value.trim() || "symbol",
    model_dir: $("model-dir").value.trim() || "packages3d",
    model_base_variable: $("model-base-variable").value.trim(),
    create_footprint: $("create-footprint").checked,
    create_symbol: $("create-symbol").checked,
    models: $("models").value,
    skip_existing: $("skip-existing").checked,
    add_to_all: $("add-to-all").checked,
  };
}

function loadUIFromConfig(cfg) {
  config = { ...DEFAULT_CONFIG, ...cfg };

  const dirList = $("dir-list");
  dirList.innerHTML = "";
  for (const dir of config.directories || []) {
    const opt = document.createElement("option");
    opt.value = dir;
    opt.textContent = dir;
    dirList.appendChild(opt);
  }

  $("symbol-lib").value = config.symbol_lib || "";
  $("footprint-lib").value = config.footprint_lib || "footprint";
  $("symbol-lib-dir").value = config.symbol_lib_dir || "symbol";
  $("model-dir").value = config.model_dir || "packages3d";
  $("model-base-variable").value = config.model_base_variable || "";
  $("create-footprint").checked = config.create_footprint;
  $("create-symbol").checked = config.create_symbol;
  $("skip-existing").checked = config.skip_existing;
  $("add-to-all").checked = config.add_to_all;

  const models = config.models || "STEP";
  const modelSelect = $("models");
  modelSelect.value = ["STEP", "WRL", "Both", "None"].includes(models)
    ? models
    : "STEP";
}

async function loadConfig() {
  try {
    const cfg = await invoke("load_config");
    loadUIFromConfig(cfg);
  } catch (err) {
    logMessage("Failed to load config: " + err);
  }
}

async function saveConfig() {
  try {
    config = getConfigFromUI();
    await invoke("save_config", { config });
  } catch (err) {
    logMessage("Failed to save config: " + err);
  }
}

async function addDirectory() {
  try {
    const selected = await open({ directory: true, multiple: false });
    if (!selected) return;
    const dirPath = Array.isArray(selected) ? selected[0] : selected;
    const dirList = $("dir-list");
    const existing = Array.from(dirList.options).map((opt) => opt.value);
    if (existing.includes(dirPath)) {
      logMessage("Directory is already registered.");
      return;
    }
    const opt = document.createElement("option");
    opt.value = dirPath;
    opt.textContent = dirPath;
    dirList.appendChild(opt);
    await saveConfig();
  } catch (err) {
    logMessage("Failed to add directory: " + err);
  }
}

async function removeDirectory() {
  const dirList = $("dir-list");
  const selected = Array.from(dirList.selectedOptions);
  for (const opt of selected) {
    dirList.remove(opt.index);
  }
  await saveConfig();
}

function getTargetDirectories() {
  const dirList = $("dir-list");
  const dirs = Array.from(dirList.options).map((opt) => opt.value);
  if (config.add_to_all) {
    return dirs;
  }
  const selected = Array.from(dirList.selectedOptions).map((opt) => opt.value);
  if (selected.length > 0) {
    return selected;
  }
  return dirs.length > 0 ? [dirs[0]] : [];
}

async function onAddComponents() {
  if (isRunning) return;

  const rawParts = $("part-numbers").value.trim();
  if (!rawParts) {
    setStatus("Please enter part number(s).");
    return;
  }

  const targetDirs = getTargetDirectories();
  if (targetDirs.length === 0) {
    setStatus("Please register/select an output directory.");
    return;
  }

  const parts = rawParts
    .replace(/,/g, " ")
    .split(/\s+/)
    .map((p) => p.trim())
    .filter((p) => p.length > 0);

  if (parts.length === 0) {
    setStatus("Please enter part number(s).");
    return;
  }

  config = getConfigFromUI();
  await saveConfig();

  clearLog();
  setRunning(true);
  setStatus(`Processing ${parts.length} part(s) into ${targetDirs.length} directorie(s)...`);

  try {
    await invoke("add_components", { config, parts, targetDirs });
    setStatus("Finished");
  } catch (err) {
    logMessage("Error: " + err);
    setStatus("Failed");
  } finally {
    setRunning(false);
  }
}

window.addEventListener("DOMContentLoaded", async () => {
  logEl = $("log-output");

  await loadConfig();

  $("add-dir-btn").addEventListener("click", addDirectory);
  $("remove-dir-btn").addEventListener("click", removeDirectory);
  $("add-btn").addEventListener("click", onAddComponents);
  $("clear-log-btn").addEventListener("click", clearLog);

  $("part-numbers").addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      onAddComponents();
    }
  });

  const saveOnChange = [
    "symbol-lib",
    "footprint-lib",
    "symbol-lib-dir",
    "model-dir",
    "model-base-variable",
    "models",
    "create-footprint",
    "create-symbol",
    "skip-existing",
    "add-to-all",
  ];
  for (const id of saveOnChange) {
    const el = $(id);
    if (!el) continue;
    el.addEventListener("change", saveConfig);
  }

  await listen("log-message", (event) => {
    logMessage(event.payload);
  });

  await listen("status-message", (event) => {
    setStatus(event.payload);
  });
});
