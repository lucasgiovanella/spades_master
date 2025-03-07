// Execution management
/**
 * SPAdes Master Web - Execução e Monitoramento
 * Gerencia a execução do SPAdes no servidor remoto
 */

// Socket.IO initialization
const socket = io();

// Estado da página
const executionState = {
  connected: false,
  uploading: false,
  running: false,
  serverInfo: null,
  selectedProfile: null,
  selectedFiles: [],
  currentJob: null,
  monitoring: false,
  monitoringTimer: null,
  startTime: null,
};

// Elementos da interface
const elements = {
  // Seleção e conexão
  serverProfile: document.getElementById("server-profile"),
  btnConnect: document.getElementById("btn-connect"),
  serverStatus: document.getElementById("server-status"),
  serverInfo: document.getElementById("server-info"),

  // Informações do servidor
  infoCpu: document.getElementById("info-cpu"),
  infoMemory: document.getElementById("info-memory"),
  infoSpades: document.getElementById("info-spades"),

  // Upload e arquivos
  readFiles: document.getElementById("read-files"),
  remoteDir: document.getElementById("remote-dir"),
  outputDir: document.getElementById("output-dir"),
  btnUploadFiles: document.getElementById("btn-upload-files"),

  // Parâmetros do SPAdes
  threads: document.getElementById("threads"),
  memory: document.getElementById("memory"),
  mode: document.getElementById("mode"),
  kmer: document.getElementById("kmer"),
  btnAdvancedParams: document.getElementById("btn-advanced-params"),
  btnRunSpades: document.getElementById("btn-run-spades"),
  // Controle de emergência
  btnCancelJob: document.getElementById("btn-cancel-job"),
  btnOpenTerminal: document.getElementById("btn-open-terminal"),
  // Monitoramento
  jobStatus: document.getElementById("job-status"),
  phaseText: document.getElementById("phase-text"),
  progressBar: document.getElementById("progress-bar"),
  elapsedTime: document.getElementById("elapsed-time"),
  jobPid: document.getElementById("job-pid"),
  cpuUsage: document.getElementById("cpu-usage"),
  cpuBar: document.getElementById("cpu-bar"),
  memoryUsage: document.getElementById("memory-usage"),
  memoryBar: document.getElementById("memory-bar"),
  // Log
  logContent: document.getElementById("log-content"),
  btnClearLog: document.getElementById("btn-clear-log"),
  btnSaveLog: document.getElementById("btn-save-log"),
  // Resultados
  resultsStatus: document.getElementById("results-status"),
  btnDownloadImportant: document.getElementById("btn-download-important"),
  btnDownloadAll: document.getElementById("btn-download-all"),
};
// Modal de parâmetros avançados
const advancedParams = {
  modal: new bootstrap.Modal(document.getElementById("advancedParamsModal")),
  form: document.getElementById("advanced-params-form"),
  mode: document.getElementById("advanced-mode"),
  threads: document.getElementById("advanced-threads"),
  memory: document.getElementById("advanced-memory"),
  kmer: document.getElementById("advanced-kmer"),
  careful: document.getElementById("advanced-careful"),
  covCutoff: document.getElementsByName("cov_cutoff"),
  covCustomValue: document.getElementById("cov-custom-value"),
  phredOffset: document.getElementsByName("phred_offset"),
  onlyErrorCorrection: document.getElementById("only-error-correction"),
  onlyAssembler: document.getElementById("only-assembler"),
  btnApply: document.getElementById("btn-apply-params"),
};
// Inicialização
document.addEventListener("DOMContentLoaded", () => {
  // Carregar lista de perfis
  loadProfiles();
  // Configurar event listeners
  setupEventListeners();
  // Configurar socket listeners
  setupSocketListeners();
});
// Carregar perfis de servidor
async function loadProfiles() {
  try {
    const response = await fetchWithErrorHandling("/api/profiles/");
    if (response.status === "success" && Array.isArray(response.profiles)) {
      // Limpar e popular o dropdown
      elements.serverProfile.innerHTML =
        '<option value="" selected>Selecione um perfil de servidor...</option>';
      response.profiles.forEach((profile) => {
        const option = document.createElement("option");
        option.value = profile;
        option.textContent = profile;
        elements.serverProfile.appendChild(option);
      });
    } else {
      throw new Error(response.message || 'Erro ao carregar perfis');
    }
  } catch (error) {
    console.error("Erro ao carregar perfis:", error);
    showToast("Erro", "Não foi possível carregar os perfis de servidor", "danger");
  }
}
// Configurar event listeners
function setupEventListeners() {
  // Botões principais
  elements.btnConnect.addEventListener("click", connectToServer);
  elements.btnUploadFiles.addEventListener("click", prepareAndUploadFiles);
  elements.btnRunSpades.addEventListener("click", runSpades);
  elements.btnCancelJob.addEventListener("click", cancelJob);
  elements.btnOpenTerminal.addEventListener("click", openSSHTerminal);
  // Seleção de arquivos
  elements.readFiles.addEventListener("change", handleFileSelection);
  // Log
  elements.btnClearLog.addEventListener("click", clearLog);
  elements.btnSaveLog.addEventListener("click", saveLog);
  // Download de resultados
  elements.btnDownloadImportant.addEventListener("click", () =>
    downloadResults(true)
  );
  elements.btnDownloadAll.addEventListener("click", () =>
    downloadResults(false)
  );
  // Parâmetros avançados
  elements.btnAdvancedParams.addEventListener("click", showAdvancedParams);
  advancedParams.btnApply.addEventListener("click", applyAdvancedParams);
  // Sync dos parâmetros básicos com avançados
  elements.mode.addEventListener(
    "change",
    () => (advancedParams.mode.value = elements.mode.value)
  );
  elements.threads.addEventListener(
    "change",
    () => (advancedParams.threads.value = elements.threads.value)
  );
  elements.memory.addEventListener(
    "change",
    () => (advancedParams.memory.value = elements.memory.value)
  );
  elements.kmer.addEventListener(
    "change",
    () => (advancedParams.kmer.value = elements.kmer.value)
  );
  // Checkbox de modo careful
  advancedParams.careful.addEventListener("change", toggleCarefulMode);
  // Radio buttons de cutoff personalizado
  Array.from(advancedParams.covCutoff).forEach((radio) => {
    radio.addEventListener("change", () => {
      if (radio.value === "custom") {
        advancedParams.covCustomValue.disabled = false;
      } else {
        advancedParams.covCustomValue.disabled = true;
      }
    });
  });
  // Checkboxes mutuamente exclusivos
  advancedParams.onlyErrorCorrection.addEventListener("change", () => {
    if (advancedParams.onlyErrorCorrection.checked) {
      advancedParams.onlyAssembler.checked = false;
    }
  });
  advancedParams.onlyAssembler.addEventListener("change", () => {
    if (advancedParams.onlyAssembler.checked) {
      advancedParams.onlyErrorCorrection.checked = false;
    }
  });
}
// Configurar listeners de socket
function setupSocketListeners() {
  // Resultado de conexão com servidor
  socket.on("connect_result", (data) => {
    executionState.connected = data.success;
    updateConnectionUI(data);
  });
  // Resultado de preparação e upload
  socket.on("prepare_result", (data) => {
    executionState.uploading = false;
    if (data.success) {
      showToast("Sucesso", "Arquivos enviados com sucesso", "success");
      elements.btnRunSpades.disabled = false;
      elements.jobStatus.className = "alert alert-info";
      elements.jobStatus.innerHTML =
        '<i class="fas fa-check-circle me-2"></i> Arquivos enviados. Pronto para executar o SPAdes.';
    } else {
      showToast("Erro", "Falha ao enviar arquivos", "danger");
      elements.jobStatus.className = "alert alert-danger";
      elements.jobStatus.innerHTML =
        '<i class="fas fa-times-circle me-2"></i> Falha ao enviar arquivos.';
    }
  });
  // Resultado de execução do SPAdes
  socket.on("run_result", (data) => {
    if (data.success) {
      executionState.running = true;
      executionState.startTime = new Date();
      executionState.currentJob = {
        pid: data.job_pid,
        id: data.job_id,
        output_file: data.job_output_file,
      };
      // Atualizar UI
      updateJobRunningUI(true);
      elements.jobStatus.className = "alert alert-success";
      elements.jobStatus.innerHTML =
        '<i class="fas fa-cog fa-spin me-2"></i> SPAdes em execução...';
      if (data.job_pid) {
        elements.jobPid.innerHTML = `PID: ${data.job_pid}`;
      }
      // Iniciar monitoramento
      startMonitoring();
    } else {
      showToast("Erro", "Falha ao iniciar SPAdes", "danger");
      elements.jobStatus.className = "alert alert-danger";
      elements.jobStatus.innerHTML =
        '<i class="fas fa-times-circle me-2"></i> Falha ao iniciar SPAdes.';
    }
  });
  // Atualizações de monitoramento
  socket.on("monitoring_update", (data) => {
    if (data.status === "running") {
      elements.elapsedTime.textContent = data.elapsed_time || "00:00:00";
      if (data.cpu_usage !== undefined) {
        const cpuPercent = Math.round(data.cpu_usage);
        elements.cpuUsage.textContent = `${cpuPercent}%`;
        elements.cpuBar.style.width = `${cpuPercent}%`;
      }
      if (data.memory_usage !== undefined && data.memory_mb !== undefined) {
        const memText = `${Math.round(data.memory_mb)} MB (${Math.round(
          data.memory_usage
        )}%)`;
        elements.memoryUsage.textContent = memText;
        elements.memoryBar.style.width = `${Math.round(data.memory_usage)}%`;
      }
    } else if (data.status === "disconnected") {
      stopMonitoring();
      elements.jobStatus.className = "alert alert-warning";
      elements.jobStatus.innerHTML =
        '<i class="fas fa-exclamation-triangle me-2"></i> Conexão com o servidor perdida.';
    }
  });
  // Atualizações de fase
  socket.on("phase_update", (data) => {
    if (data.phase) {
      elements.phaseText.textContent = data.phase;
      // Atualizar também a barra de progresso
      const progressSteps = [
        "Command line",
        "K-mer counting",
        "Error correction",
        "Assembling",
        "Scaffolding",
      ];
      // Tentar estimar o progresso com base na fase
      let progressPercent = 0;
      for (let i = 0; i < progressSteps.length; i++) {
        if (data.phase.includes(progressSteps[i])) {
          progressPercent = Math.round(((i + 1) / progressSteps.length) * 100);
          break;
        }
      }
      // Atualizar barra (mínimo 10% para mostrar algum progresso)
      progressPercent = Math.max(10, progressPercent);
      elements.progressBar.style.width = `${progressPercent}%`;
      elements.progressBar.textContent = `${progressPercent}%`;
    }
  });
  // Job finalizado
  socket.on("job_completed", (data) => {
    stopMonitoring();
    executionState.running = false;
    // Atualizar UI
    updateJobRunningUI(false);
    if (data.success) {
      elements.jobStatus.className = "alert alert-success";
      elements.jobStatus.innerHTML =
        '<i class="fas fa-check-circle me-2"></i> Montagem concluída com sucesso!';
      // Habilitar botões de download
      elements.btnDownloadImportant.disabled = false;
      elements.btnDownloadAll.disabled = false;
      elements.resultsStatus.className = "alert alert-success";
      elements.resultsStatus.innerHTML =
        '<i class="fas fa-check-circle me-2"></i> Montagem concluída. Baixe os resultados.';
    } else {
      elements.jobStatus.className = "alert alert-danger";
      elements.jobStatus.innerHTML =
        '<i class="fas fa-times-circle me-2"></i> A montagem falhou. Verifique o log para mais detalhes.';
    }
  });
  // Resultado de cancelamento
  socket.on("cancel_result", (data) => {
    stopMonitoring();
    executionState.running = false;
    // Atualizar UI
    updateJobRunningUI(false);
    elements.jobStatus.className = "alert alert-warning";
    elements.jobStatus.innerHTML =
      '<i class="fas fa-ban me-2"></i> Job cancelado pelo usuário.';
  });
  // Resultado de download
  socket.on("download_result", (data) => {
    if (data.success) {
      showToast("Sucesso", "Download concluído com sucesso", "success");
      elements.resultsStatus.className = "alert alert-success";
      elements.resultsStatus.innerHTML =
        '<i class="fas fa-check-circle me-2"></i> Download concluído. Arquivos salvos em: ' +
        data.local_dir;
    } else {
      showToast("Erro", "Falha ao baixar resultados", "danger");
    }
  });
}
// Conectar ao servidor
async function connectToServer() {
  const profileName = elements.serverProfile.value;
  if (!profileName) {
    showToast("Aviso", "Por favor, selecione um perfil de servidor", "warning");
    return;
  }
  executionState.selectedProfile = profileName;
  try {
    // Atualizar UI
    elements.btnConnect.disabled = true;
    elements.btnConnect.innerHTML =
      '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Conectando...';
    elements.serverStatus.textContent = "Status: Conectando...";
    // Enviar requisição para conectar
    const response = await fetchWithErrorHandling("/api/execution/connect", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ profile_name: profileName }),
    });
    if (response.status === "success") {
      // O resultado real virá via socket
      showToast("Conectando", "Tentando conectar ao servidor...", "info");
    } else {
      throw new Error(response.message || "Falha ao iniciar conexão");
    }
  } catch (error) {
    showToast("Erro", error.message, "danger");
    // Resetar UI
    elements.btnConnect.disabled = false;
    elements.btnConnect.innerHTML = '<i class="fas fa-plug me-1"></i> Conectar';
    elements.serverStatus.textContent = "Status: Desconectado";
  }
}
// Atualizar UI após conexão
function updateConnectionUI(data) {
  elements.btnConnect.disabled = false;
  if (data.success) {
    elements.btnConnect.innerHTML =
      '<i class="fas fa-check me-1"></i> Conectado';
    elements.serverStatus.textContent = "Status: Conectado";
    elements.btnOpenTerminal.disabled = false;
    elements.btnUploadFiles.disabled = false;
    // Mostrar informações do servidor
    elements.serverInfo.classList.remove("d-none");
    if (data.resources) {
      elements.infoCpu.textContent = data.resources.cpu_count;
      if (typeof data.resources.total_mem === "number") {
        const memGB = (data.resources.total_mem / 1024).toFixed(1);
        elements.infoMemory.textContent = `${data.resources.total_mem} MB (${memGB} GB)`;
      } else {
        elements.infoMemory.textContent = data.resources.total_mem;
      }
      if (data.spades_path) {
        elements.infoSpades.textContent = data.spades_path;
        elements.infoSpades.classList.add("text-success");
      } else {
        elements.infoSpades.textContent = "Não encontrado";
        elements.infoSpades.classList.add("text-danger");
      }
    }
  } else {
    elements.btnConnect.innerHTML = '<i class="fas fa-plug me-1"></i> Conectar';
    elements.serverStatus.textContent = "Status: Desconectado";
    showToast("Erro", "Falha ao conectar com o servidor", "danger");
  }
}
// Manipular seleção de arquivos
function handleFileSelection(event) {
  const files = event.target.files;
  if (files.length > 0) {
    // Armazenar referências aos arquivos selecionados
    executionState.selectedFiles = Array.from(files);
    // Verificar se temos pelo menos 2 arquivos (paired-end)
    if (executionState.selectedFiles.length >= 2) {
      // Verificar se podemos identificar R1 e R2
      let r1File = null;
      let r2File = null;
      for (const file of executionState.selectedFiles) {
        const fileName = file.name.toLowerCase();
        if (fileName.includes("_r1") || fileName.includes("_1.")) {
          r1File = file;
        } else if (fileName.includes("_r2") || fileName.includes("_2.")) {
          r2File = file;
        }
      }
      if (r1File && r2File) {
        showToast(
          "Arquivos",
          `Identificados: R1=${r1File.name}, R2=${r2File.name}`,
          "success"
        );
      }
    }
  }
}
// Preparar e enviar arquivos
async function prepareAndUploadFiles() {
  if (!executionState.connected) {
    showToast("Aviso", "Conecte-se primeiro ao servidor", "warning");
    return;
  }
  if (executionState.selectedFiles.length === 0) {
    showToast("Aviso", "Selecione os arquivos de leitura", "warning");
    return;
  }
  // Verificar diretório remoto
  const remoteDir = elements.remoteDir.value.trim();
  if (!remoteDir) {
    showToast("Aviso", "Informe o diretório remoto", "warning");
    return;
  }
  try {
    // Atualizar UI
    elements.btnUploadFiles.disabled = true;
    elements.btnUploadFiles.innerHTML =
      '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Enviando...';
    executionState.uploading = true;
    // Criar um FormData para upload de arquivos
    const formData = new FormData();
    executionState.selectedFiles.forEach((file) => {
      formData.append("reads", file);
    });
    // Enviar arquivos
    const uploadResponse = await fetch("/api/execution/upload", {
      method: "POST",
      body: formData,
    });
    if (!uploadResponse.ok) {
      throw new Error("Falha ao fazer upload dos arquivos");
    }
    const uploadResult = await uploadResponse.json();
    if (uploadResult.status !== "success") {
      throw new Error(
        uploadResult.message || "Falha ao fazer upload dos arquivos"
      );
    }
    // Arquivos enviados, agora preparar o diretório remoto e transferir
    const prepareResponse = await fetchWithErrorHandling(
      "/api/execution/prepare",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          remote_dir: remoteDir,
          file_paths: uploadResult.files.map((f) => f.path),
        }),
      }
    );
    if (prepareResponse.status === "success") {
      // O resultado real virá via socket
      elements.jobStatus.className = "alert alert-info";
      elements.jobStatus.innerHTML =
        '<i class="fas fa-sync fa-spin me-2"></i> Enviando arquivos para o servidor...';
    } else {
      throw new Error(prepareResponse.message || "Falha ao preparar arquivos");
    }
  } catch (error) {
    showToast("Erro", error.message, "danger");
    // Resetar UI
    executionState.uploading = false;
    elements.btnUploadFiles.disabled = false;
    elements.btnUploadFiles.innerHTML =
      '<i class="fas fa-upload me-1"></i> Preparar e Enviar Arquivos';
  }
}
// Executar SPAdes
async function runSpades() {
  if (!executionState.connected) {
    showToast("Aviso", "Conecte-se primeiro ao servidor", "warning");
    return;
  }
  if (executionState.running) {
    showToast("Aviso", "Já existe um job em execução", "warning");
    return;
  }
  // Verificar parâmetros obrigatórios
  const remoteDir = elements.remoteDir.value.trim();
  const outputDir = elements.outputDir.value.trim();
  const threads = elements.threads.value.trim();
  if (!remoteDir || !outputDir || !threads) {
    showToast("Aviso", "Verifique os parâmetros obrigatórios", "warning");
    return;
  }
  // Obter nomes dos arquivos de leitura
  if (executionState.selectedFiles.length < 2) {
    showToast("Aviso", "Selecione os arquivos de leitura R1 e R2", "warning");
    return;
  }
  // Tentar identificar R1 e R2
  let r1File = null;
  let r2File = null;
  for (const file of executionState.selectedFiles) {
    const fileName = file.name.toLowerCase();
    if (fileName.includes("_r1") || fileName.includes("_1.")) {
      r1File = file;
    } else if (fileName.includes("_r2") || fileName.includes("_2.")) {
      r2File = file;
    }
  }
  if (!r1File || !r2File) {
    r1File = executionState.selectedFiles[0];
    r2File = executionState.selectedFiles[1];
  }
  try {
    // Atualizar UI
    elements.btnRunSpades.disabled = true;
    elements.btnRunSpades.innerHTML =
      '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Iniciando...';
    // Montar parâmetros
    const params = {
      remote_dir: remoteDir,
      read1: r1File.name,
      read2: r2File.name,
      output_dir: outputDir,
      threads: threads,
      memory: elements.memory.value.trim(),
      mode: elements.mode.value,
      kmer: elements.kmer.value.trim(),
    };
    // Incluir parâmetros avançados, se configurados
    const advParams = getAdvancedParams();
    const spadeParams = { ...params, ...advParams };
    // Enviar requisição
    const response = await fetchWithErrorHandling("/api/execution/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(spadeParams),
    });
    if (response.status === "success") {
      // O resultado real virá via socket
      elements.jobStatus.className = "alert alert-info";
      elements.jobStatus.innerHTML =
        '<i class="fas fa-cog fa-spin me-2"></i> Iniciando SPAdes...';
    } else {
      throw new Error(response.message || "Falha ao iniciar SPAdes");
    }
  } catch (error) {
    showToast("Erro", error.message, "danger");
    // Resetar UI
    elements.btnRunSpades.disabled = false;
    elements.btnRunSpades.innerHTML =
      '<i class="fas fa-play-circle me-1"></i> Executar SPAdes';
  }
}
// Obter parâmetros avançados configurados
function getAdvancedParams() {
  const params = {};
  // Cobrir parâmetros avançados se foram modificados
  // Cutoff de cobertura
  const covCutoff = Array.from(advancedParams.covCutoff).find((r) => r.checked);
  if (covCutoff) {
    if (covCutoff.value === "custom" && advancedParams.covCustomValue.value) {
      params.cov_cutoff = advancedParams.covCustomValue.value;
    } else if (covCutoff.value !== "auto") {
      params.cov_cutoff = covCutoff.value;
    }
  }
  // Offset de Phred
  const phredOffset = Array.from(advancedParams.phredOffset).find(
    (r) => r.checked
  );
  if (phredOffset && phredOffset.value !== "auto") {
    params.phred_offset = phredOffset.value;
  }
  // Opções de pipeline
  if (advancedParams.onlyErrorCorrection.checked) {
    params.only_error_correction = true;
  }
  if (advancedParams.onlyAssembler.checked) {
    params.only_assembler = true;
  }
  return params;
}
// Cancelar job em execução
async function cancelJob() {
  if (!executionState.connected || !executionState.running) {
    showToast("Aviso", "Não há job em execução para cancelar", "warning");
    return;
  }
  if (!confirm("Tem certeza que deseja cancelar o job em execução?")) {
    return;
  }
  try {
    // Atualizar UI
    elements.btnCancelJob.disabled = true;
    elements.btnCancelJob.innerHTML =
      '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Cancelando...';
    // Enviar requisição
    const response = await fetchWithErrorHandling("/api/execution/cancel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });
    if (response.status === "success") {
      // O resultado real virá via socket
      elements.jobStatus.className = "alert alert-warning";
      elements.jobStatus.innerHTML =
        '<i class="fas fa-hourglass-half me-2"></i> Cancelando job...';
    } else {
      throw new Error(response.message || "Falha ao cancelar job");
    }
  } catch (error) {
    showToast("Erro", error.message, "danger");
    // Resetar UI
    elements.btnCancelJob.disabled = false;
    elements.btnCancelJob.innerHTML =
      '<i class="fas fa-stop-circle me-1"></i> Cancelar Job';
  }
}
// Abrir terminal SSH
async function openSSHTerminal() {
  if (!executionState.connected) {
    showToast("Aviso", "Conecte-se primeiro ao servidor", "warning");
    return;
  }
  try {
    const profileName = executionState.selectedProfile;
    if (!profileName) {
      throw new Error("Perfil de servidor não selecionado");
    }
    // Enviar requisição
    const response = await fetchWithErrorHandling(
      `/api/profiles/${profileName}/terminal`,
      {
        method: "POST",
      }
    );
    if (response.status === "success") {
      showToast("Sucesso", "Terminal SSH aberto", "success");
    } else {
      throw new Error(response.message || "Falha ao abrir terminal SSH");
    }
  } catch (error) {
    showToast("Erro", error.message, "danger");
  }
}
// Baixar resultados
async function downloadResults(importantOnly = true) {
  if (!executionState.connected) {
    showToast("Aviso", "Conecte-se primeiro ao servidor", "warning");
    return;
  }
  // Verificar parâmetros obrigatórios
  const remoteDir = elements.remoteDir.value.trim();
  const outputDir = elements.outputDir.value.trim();
  if (!remoteDir || !outputDir) {
    showToast("Aviso", "Verifique os diretórios remoto e de saída", "warning");
    return;
  }
  try {
    // Atualizar UI
    const btnElement = importantOnly
      ? elements.btnDownloadImportant
      : elements.btnDownloadAll;
    btnElement.disabled = true;
    btnElement.innerHTML =
      '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Baixando...';
    // Enviar requisição
    const response = await fetchWithErrorHandling("/api/results/download", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        remote_dir: remoteDir,
        output_dir: outputDir,
        important_only: importantOnly,
      }),
    });
    if (response.status === "success") {
      // O resultado real virá via socket
      elements.resultsStatus.className = "alert alert-info";
      elements.resultsStatus.innerHTML =
        '<i class="fas fa-sync fa-spin me-2"></i> Baixando resultados...';
    } else {
      throw new Error(response.message || "Falha ao baixar resultados");
    }
  } catch (error) {
    showToast("Erro", error.message, "danger");
    // Resetar UI
    const btnElement = importantOnly
      ? elements.btnDownloadImportant
      : elements.btnDownloadAll;
    btnElement.disabled = false;
    btnElement.innerHTML = `<i class="fas fa-download me-1"></i> Baixar ${
      importantOnly ? "Arquivos Importantes" : "Todos os Arquivos"
    }`;
  } finally {
    // Re-habilitar os botões após um tempo
    setTimeout(() => {
      elements.btnDownloadImportant.disabled = false;
      elements.btnDownloadAll.disabled = false;
      elements.btnDownloadImportant.innerHTML =
        '<i class="fas fa-download me-1"></i> Baixar Arquivos Importantes';
      elements.btnDownloadAll.innerHTML =
        '<i class="fas fa-download me-1"></i> Baixar Todos os Arquivos';
    }, 3000);
  }
}
// Iniciar monitoramento
function startMonitoring() {
  executionState.monitoring = true;
  // Iniciar barra de progresso
  elements.progressBar.style.width = "10%";
  elements.progressBar.textContent = "Iniciando...";
  // Inicializar contadores
  elements.elapsedTime.textContent = "00:00:00";
  elements.cpuUsage.textContent = "0%";
  elements.memoryUsage.textContent = "0 MB";
  elements.cpuBar.style.width = "0%";
  elements.memoryBar.style.width = "0%";
  // Não precisamos criar um timer aqui, pois as atualizações virão via socket
}
// Parar monitoramento
function stopMonitoring() {
  executionState.monitoring = false;
  // Parar o timer local se estiver rodando
  if (executionState.monitoringTimer) {
    clearInterval(executionState.monitoringTimer);
    executionState.monitoringTimer = null;
  }
}
// Atualizar UI quando job está rodando/parado
function updateJobRunningUI(running) {
  if (running) {
    elements.btnRunSpades.disabled = true;
    elements.btnCancelJob.disabled = false;
    elements.btnUploadFiles.disabled = true;
    elements.btnDownloadImportant.disabled = true;
    elements.btnDownloadAll.disabled = true;
  } else {
    elements.btnRunSpades.disabled = false;
    elements.btnRunSpades.innerHTML =
      '<i class="fas fa-play-circle me-1"></i> Executar SPAdes';
    elements.btnCancelJob.disabled = true;
    elements.btnUploadFiles.disabled = false;
  }
}
// Mostrar parâmetros avançados
function showAdvancedParams() {
  // Sincronizar valores básicos com avançados
  advancedParams.mode.value = elements.mode.value;
  advancedParams.threads.value = elements.threads.value;
  advancedParams.memory.value = elements.memory.value;
  advancedParams.kmer.value = elements.kmer.value;
  // Sincronizar modo careful com checkbox
  advancedParams.careful.checked = elements.mode.value === "careful";
  // Mostrar modal
  advancedParams.modal.show();
}
// Aplicar parâmetros avançados
function applyAdvancedParams() {
  // Atualizar valores básicos
  elements.mode.value = advancedParams.mode.value;
  elements.threads.value = advancedParams.threads.value;
  elements.memory.value = advancedParams.memory.value;
  elements.kmer.value = advancedParams.kmer.value;
  // Se modo careful estiver marcado, garantir que o modo selecionado é careful
  if (advancedParams.careful.checked && elements.mode.value !== "careful") {
    elements.mode.value = "careful";
  }
  // Fechar modal
  advancedParams.modal.hide();
  showToast("Parâmetros", "Parâmetros avançados aplicados", "success");
}
// Toggle modo careful
function toggleCarefulMode() {
  if (advancedParams.careful.checked) {
    advancedParams.mode.value = "careful";
  } else if (advancedParams.mode.value === "careful") {
    advancedParams.mode.value = "isolate";
  }
}
// Limpar log
function clearLog() {
  elements.logContent.innerHTML = "";
  showToast("Log", "Log limpo", "info");
}
// Salvar log
function saveLog() {
  // Obter conteúdo do log
  const logText = Array.from(elements.logContent.querySelectorAll(".log-entry"))
    .map((entry) => {
      const timestamp = entry.querySelector(".log-timestamp").textContent;
      const level = entry.querySelector(".log-level").textContent;
      const message = entry.querySelector(".log-message").textContent;
      return `[${timestamp}] [${level}] ${message}`;
    })
    .join("\n");
  // Criar blob e link para download
  const blob = new Blob([logText], { type: "text/plain" });
  const url = URL.createObjectURL(blob);
  // Criar link temporário e clicar nele
  const a = document.createElement("a");
  a.href = url;
  a.download = `spades_log_${new Date()
    .toISOString()
    .replace(/[:.]/g, "-")}.txt`;
  document.body.appendChild(a);
  a.click();
  // Limpar
  setTimeout(() => {
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, 100);
  showToast("Log", "Log salvo", "success");
}
