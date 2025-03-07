// Results visualization 
/**
 * SPAdes Master Web - Resultados
 * Visualização e gerenciamento de resultados de montagens
 */

// Estado da página
const resultsState = {
    results: [],
    selectedResult: null,
    files: [],
    fileContent: null,
    serverConnected: false
};

// Elementos da interface
const elements = {
    resultsTableBody: document.getElementById('results-table-body'),
    filesPlaceholder: document.getElementById('files-placeholder'),
    filesList: document.getElementById('files-list'),
    mainFilesBody: document.getElementById('main-files-body'),
    allFilesBody: document.getElementById('all-files-body'),
    btnDownloadAllFiles: document.getElementById('btn-download-all-files'),
    btnDeleteAssembly: document.getElementById('btn-delete-assembly'),
    
    // Detalhes da montagem
    assemblyDetailsPlaceholder: document.getElementById('assembly-details-placeholder'),
    assemblyDetails: document.getElementById('assembly-details'),
    statsContigs: document.getElementById('stats-contigs'),
    statsLength: document.getElementById('stats-length'),
    statsN50: document.getElementById('stats-n50'),
    statsGC: document.getElementById('stats-gc'),
    statsLongest: document.getElementById('stats-longest'),
    statsMode: document.getElementById('stats-mode'),
    statsVersion: document.getElementById('stats-version'),
    btnViewCmd: document.getElementById('btn-view-cmd'),
    btnDownloadReport: document.getElementById('btn-download-report'),
    
    // Modal de visualização de arquivo
    fileViewModal: new bootstrap.Modal(document.getElementById('fileViewModal')),
    fileViewModalLabel: document.getElementById('fileViewModalLabel'),
    fileViewType: document.getElementById('file-view-type'),
    fileViewSize: document.getElementById('file-view-size'),
    fileContent: document.getElementById('file-content'),
    btnDownloadViewedFile: document.getElementById('btn-download-viewed-file'),
    
    // Modal de comando SPAdes
    cmdModal: new bootstrap.Modal(document.getElementById('cmdModal')),
    spadesCommand: document.getElementById('spades-command'),
    btnCopyCmd: document.getElementById('btn-copy-cmd'),
    
    // Modal de confirmação de exclusão
    deleteModal: new bootstrap.Modal(document.getElementById('deleteModal')),
    deleteAssemblyName: document.getElementById('delete-assembly-name'),
    btnConfirmDelete: document.getElementById('btn-confirm-delete')
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    // Carregar resultados
    loadResults();
    
    // Configurar event listeners
    setupEventListeners();
    
    // Verificar conexão atual
    checkConnection();
});

// Carregar resultados disponíveis
async function loadResults() {
    try {
        showLoadingInTable();
        
        const response = await fetchWithErrorHandling('/api/results/list');
        
        if (response.status === 'success') {
            resultsState.results = response.results;
            renderResultsTable();
        }
    } catch (error) {
        console.error('Erro ao carregar resultados:', error);
        showErrorInTable('Não foi possível carregar resultados. Tente recarregar a página.');
    }
}

// Configurar event listeners
function setupEventListeners() {
    // Botões da interface de detalhes
    elements.btnViewCmd.addEventListener('click', showCommandModal);
    elements.btnDownloadReport.addEventListener('click', downloadReport);
    elements.btnCopyCmd.addEventListener('click', () => copyToClipboard(elements.spadesCommand.textContent));
    
    // Botões de arquivos
    elements.btnDownloadAllFiles.addEventListener('click', downloadAllFiles);
    elements.btnDeleteAssembly.addEventListener('click', confirmDeleteAssembly);
    
    // Modal de exclusão
    elements.btnConfirmDelete.addEventListener('click', deleteAssembly);
    
    // Modal de visualização de arquivo
    elements.btnDownloadViewedFile.addEventListener('click', downloadViewedFile);
}

// Verificar status da conexão
async function checkConnection() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.status === 'online') {
            resultsState.serverConnected = socket.connected;
        }
    } catch (error) {
        resultsState.serverConnected = false;
        console.error('Erro ao verificar status da conexão:', error);
    }
}

// Renderizar tabela de resultados
function renderResultsTable() {
    const tableBody = elements.resultsTableBody;
    tableBody.innerHTML = '';
    
    if (resultsState.results.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">
                    <div class="alert alert-info my-3">
                        <i class="fas fa-info-circle me-2"></i>
                        Nenhum resultado de montagem encontrado.
                    </div>
                    <a href="/execution" class="btn btn-primary btn-sm">
                        <i class="fas fa-play-circle me-1"></i> Executar Nova Montagem
                    </a>
                </td>
            </tr>
        `;
        return;
    }
    
    // Ordenar resultados por data, mais recentes primeiro
    const sortedResults = [...resultsState.results].sort((a, b) => {
        // Converter strings de data em objetos Date
        const dateA = a.date ? new Date(a.date) : new Date(0);
        const dateB = b.date ? new Date(b.date) : new Date(0);
        return dateB - dateA;
    });
    
    // Adicionar cada resultado à tabela
    sortedResults.forEach(result => {
        const row = document.createElement('tr');
        row.classList.add('result-row');
        row.dataset.result = result.name;
        
        // Formatar data
        let dateDisplay = 'Data desconhecida';
        if (result.date) {
            const date = new Date(result.date);
            dateDisplay = date.toLocaleString();
        }
        
        // Formatar estatísticas
        const contigCount = result.stats && result.stats.scaffold_count ? 
            formatNumber(result.stats.scaffold_count) : '-';
            
        const totalLength = result.stats && result.stats.total_length ? 
            formatSizeWithUnit(result.stats.total_length) : '-';
            
        const n50 = result.stats && result.stats.n50 ? 
            formatSizeWithUnit(result.stats.n50) : '-';
        
        // Células da tabela
        row.innerHTML = `
            <td>
                <strong>${result.name}</strong>
                ${result.has_scaffolds ? '<span class="badge bg-success ms-2">Completa</span>' : ''}
            </td>
            <td>${dateDisplay}</td>
            <td>${contigCount}</td>
            <td>${totalLength}</td>
            <td>${n50}</td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary btn-view" title="Ver Detalhes">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn btn-outline-success btn-download" title="Baixar">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="btn btn-outline-danger btn-delete" title="Excluir">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        // Adicionar a linha à tabela
        tableBody.appendChild(row);
    });
    
    // Adicionar event listeners para os botões e linhas
    addTableEventListeners();
}

// Adicionar event listeners para a tabela
function addTableEventListeners() {
    // Clicar na linha para selecionar
    document.querySelectorAll('.result-row').forEach(row => {
        row.addEventListener('click', function(event) {
            // Ignorar se o clique foi em um botão
            if (event.target.closest('button')) {
                return;
            }
            
            selectResult(this.dataset.result);
        });
    });
    
    // Botões de visualização
    document.querySelectorAll('.btn-view').forEach(button => {
        button.addEventListener('click', function() {
            const resultName = this.closest('tr').dataset.result;
            selectResult(resultName);
        });
    });
    
    // Botões de download
    document.querySelectorAll('.btn-download').forEach(button => {
        button.addEventListener('click', function() {
            const resultName = this.closest('tr').dataset.result;
            createDownloadZip(resultName);
        });
    });
    
    // Botões de exclusão
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', function() {
            const resultName = this.closest('tr').dataset.result;
            confirmDeleteAssembly(resultName);
        });
    });
}

// Selecionar um resultado para visualização
async function selectResult(resultName) {
    if (resultsState.selectedResult === resultName && resultsState.files.length > 0) {
        return; // Já selecionado
    }
    
    try {
        // Marcar a linha como selecionada
        document.querySelectorAll('.result-row').forEach(row => {
            if (row.dataset.result === resultName) {
                row.classList.add('table-primary');
            } else {
                row.classList.remove('table-primary');
            }
        });
        
        // Mostrar loading
        elements.filesPlaceholder.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary mb-3"></div>
                <p class="lead text-muted">Carregando arquivos...</p>
            </div>
        `;
        elements.filesPlaceholder.classList.remove('d-none');
        elements.filesList.classList.add('d-none');
        
        // Mostrar loading nos detalhes também
        elements.assemblyDetailsPlaceholder.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary mb-3"></div>
                <p class="lead text-muted">Carregando informações...</p>
            </div>
        `;
        elements.assemblyDetailsPlaceholder.classList.remove('d-none');
        elements.assemblyDetails.classList.add('d-none');
        
        // Habilitar botões
        elements.btnDownloadAllFiles.disabled = false;
        elements.btnDeleteAssembly.disabled = false;
        
        // Obter lista de arquivos
        const response = await fetchWithErrorHandling(`/api/results/files/${resultName}`);
        
        if (response.status === 'success') {
            resultsState.selectedResult = resultName;
            resultsState.files = response.files;
            
            // Mostrar arquivos
            renderFilesList();
            
            // Obter e exibir estatísticas da montagem
            const result = resultsState.results.find(r => r.name === resultName);
            if (result && result.stats) {
                renderAssemblyDetails(result);
            } else {
                await analyzeAssembly(resultName);
            }
        } else {
            throw new Error(response.message || 'Erro ao carregar arquivos');
        }
    } catch (error) {
        console.error('Erro ao selecionar resultado:', error);
        
        // Mostrar erro
        elements.filesPlaceholder.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-exclamation-triangle text-danger fa-3x mb-3"></i>
                <p class="lead text-danger">Erro ao carregar arquivos</p>
                <p class="text-muted">${error.message}</p>
                <button class="btn btn-outline-primary" onclick="selectResult('${resultName}')">
                    <i class="fas fa-sync me-1"></i> Tentar Novamente
                </button>
            </div>
        `;
    }
}

// Renderizar lista de arquivos
function renderFilesList() {
    // Limpar listas
    elements.mainFilesBody.innerHTML = '';
    elements.allFilesBody.innerHTML = '';
    
    // Verificar se há arquivos
    if (resultsState.files.length === 0) {
        elements.filesPlaceholder.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-file-excel fa-3x text-muted mb-3"></i>
                <p class="lead text-muted">Nenhum arquivo encontrado</p>
            </div>
        `;
        elements.filesPlaceholder.classList.remove('d-none');
        elements.filesList.classList.add('d-none');
        return;
    }
    
    // Ordenar arquivos: principais primeiro, depois por nome
    const mainFiles = [
        'scaffolds.fasta', 
        'contigs.fasta', 
        'assembly_graph.fastg', 
        'spades.log',
        'contigs.paths',
        'scaffolds.paths',
        'assembly_graph_with_scaffolds.gfa',
        'params.txt',
        'input_dataset.yaml'
    ];
    
    // Mostrar arquivos principais
    mainFiles.forEach(filename => {
        const file = resultsState.files.find(f => f.name === filename);
        if (file) {
            addFileToTable(file, elements.mainFilesBody);
        }
    });
    
    // Se não houver arquivos principais, mostrar mensagem
    if (elements.mainFilesBody.children.length === 0) {
        elements.mainFilesBody.innerHTML = `
            <tr>
                <td colspan="3" class="text-center text-muted">
                    Nenhum arquivo principal encontrado
                </td>
            </tr>
        `;
    }
    
    // Mostrar todos os arquivos
    resultsState.files.forEach(file => {
        addFileToTable(file, elements.allFilesBody);
    });
    
    // Mostrar a lista
    elements.filesPlaceholder.classList.add('d-none');
    elements.filesList.classList.remove('d-none');
}

// Adicionar arquivo à tabela
function addFileToTable(file, tableBody) {
    const row = document.createElement('tr');
    
    // Determinar ícone baseado na extensão
    const extension = file.name.split('.').pop().toLowerCase();
    let iconClass = 'icon-other';
    
    if (file.name.endsWith('.fasta') || file.name.endsWith('.fa')) {
        iconClass = 'icon-fasta';
    } else if (file.name.endsWith('.fastg')) {
        iconClass = 'icon-fastg';
    } else if (file.name.endsWith('.gfa')) {
        iconClass = 'icon-gfa';
    } else if (file.name.endsWith('.txt') || file.name.endsWith('.yaml')) {
        iconClass = 'icon-txt';
    } else if (file.name.endsWith('.log')) {
        iconClass = 'icon-log';
    }
    
    // Células da tabela
    row.innerHTML = `
        <td>
            <i class="fas fa-file file-icon ${iconClass}"></i>
            ${file.name}
        </td>
        <td>${formatFileSize(file.size)}</td>
        <td>
            <div class="btn-group btn-group-sm">
                <button class="btn btn-outline-primary btn-view-file" data-file="${file.name}" title="Visualizar">
                    <i class="fas fa-eye"></i>
                </button>
                <a href="/api/results/file/${resultsState.selectedResult}/${file.name}" 
                   class="btn btn-outline-success" 
                   download="${file.name}" 
                   title="Baixar">
                    <i class="fas fa-download"></i>
                </a>
            </div>
        </td>
    `;
    
    // Adicionar a linha à tabela
    tableBody.appendChild(row);
    
    // Adicionar event listener para visualização
    row.querySelector('.btn-view-file').addEventListener('click', () => {
        viewFile(file.name);
    });
}

// Visualizar conteúdo de um arquivo
async function viewFile(filename) {
    try {
        // Determinar tipo de arquivo
        let fileType = 'text/plain';
        let canPreview = true;
        
        if (filename.endsWith('.fasta') || filename.endsWith('.fa') || filename.endsWith('.fastq') || filename.endsWith('.fq')) {
            fileType = 'text/plain';
        } else if (filename.endsWith('.png') || filename.endsWith('.jpg') || filename.endsWith('.jpeg') || filename.endsWith('.gif')) {
            fileType = `image/${filename.split('.').pop().toLowerCase()}`;
            canPreview = false;
        } else if (filename.endsWith('.pdf')) {
            fileType = 'application/pdf';
            canPreview = false;
        } else if (filename.endsWith('.fastg') || filename.endsWith('.gfa')) {
            fileType = 'text/plain'; // Também poderia ser visualizado como imagem com um visualizador específico
        }
        
        // Verificar se é um arquivo binário ou muito grande
        const file = resultsState.files.find(f => f.name === filename);
        const isBinary = file && file.size > 1024 * 1024; // Considerar arquivos maiores que 1MB como binários
        
        // Configurar modal
        elements.fileViewModalLabel.textContent = filename;
        elements.fileViewType.textContent = fileType;
        elements.fileViewSize.textContent = file ? formatFileSize(file.size) : '?';
        elements.btnDownloadViewedFile.href = `/api/results/file/${resultsState.selectedResult}/${filename}`;
        elements.btnDownloadViewedFile.download = filename;
        
        // Mostrar preview ou mensagem
        if (!canPreview || isBinary) {
            elements.fileContent.textContent = "Este arquivo não pode ser visualizado no navegador. Use o botão 'Baixar' para salvá-lo.";
            elements.fileViewModal.show();
            return;
        }
        
        // Mostrar loading
        elements.fileContent.textContent = "Carregando...";
        elements.fileViewModal.show();
        
        // Obter conteúdo do arquivo
        const response = await fetch(`/api/results/file/${resultsState.selectedResult}/${filename}`);
        
        if (!response.ok) {
            throw new Error(`Erro ao carregar arquivo: ${response.statusText}`);
        }
        
        // Verificar se o arquivo é texto
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('text')) {
            const text = await response.text();
            
            // Limitar tamanho para não travar o navegador
            if (text.length > 100000) {
                elements.fileContent.textContent = text.substring(0, 100000) + 
                    "\n\n[... Conteúdo truncado. O arquivo é muito grande para visualização completa. Use o botão 'Baixar' para ver o arquivo completo. ...]";
            } else {
                elements.fileContent.textContent = text;
            }
        } else {
            elements.fileContent.textContent = "Este arquivo não é um arquivo de texto. Use o botão 'Baixar' para salvá-lo.";
        }
    } catch (error) {
        console.error('Erro ao visualizar arquivo:', error);
        elements.fileContent.textContent = `Erro ao carregar arquivo: ${error.message}`;
    }
}

// Analisar montagem
async function analyzeAssembly(resultName) {
    try {
        const response = await fetchWithErrorHandling(`/api/results/analyze/${resultName}`);
        
        if (response.status === 'success') {
            // Encontrar o resultado na lista
            const resultIndex = resultsState.results.findIndex(r => r.name === resultName);
            
            if (resultIndex !== -1) {
                // Atualizar estatísticas
                resultsState.results[resultIndex].stats = response.stats;
                
                // Exibir detalhes
                renderAssemblyDetails(resultsState.results[resultIndex]);
            } else {
                throw new Error('Resultado não encontrado na lista');
            }
        } else {
            throw new Error(response.message || 'Erro ao analisar montagem');
        }
    } catch (error) {
        console.error('Erro ao analisar montagem:', error);
        
        // Mostrar erro
        elements.assemblyDetailsPlaceholder.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-exclamation-triangle text-danger fa-3x mb-3"></i>
                <p class="lead text-danger">Erro ao analisar montagem</p>
                <p class="text-muted">${error.message}</p>
                <button class="btn btn-outline-primary" onclick="analyzeAssembly('${resultName}')">
                    <i class="fas fa-sync me-1"></i> Tentar Novamente
                </button>
            </div>
        `;
        elements.assemblyDetailsPlaceholder.classList.remove('d-none');
        elements.assemblyDetails.classList.add('d-none');
    }
}

// Renderizar detalhes da montagem
function renderAssemblyDetails(result) {
    if (!result || !result.stats) {
        // Mostrar mensagem de erro
        elements.assemblyDetailsPlaceholder.innerHTML = `
            <div class="text-center py-5">
                <i class="fas fa-exclamation-triangle text-warning fa-3x mb-3"></i>
                <p class="lead text-warning">Sem estatísticas disponíveis</p>
                <button class="btn btn-outline-primary" onclick="analyzeAssembly('${result.name}')">
                    <i class="fas fa-sync me-1"></i> Analisar Montagem
                </button>
            </div>
        `;
        elements.assemblyDetailsPlaceholder.classList.remove('d-none');
        elements.assemblyDetails.classList.add('d-none');
        return;
    }
    
    const stats = result.stats;
    
    // Preencher estatísticas
    elements.statsContigs.textContent = stats.scaffold_count ? formatNumber(stats.scaffold_count) : '-';
    elements.statsLength.textContent = stats.total_length ? formatSizeWithUnit(stats.total_length) : '-';
    elements.statsN50.textContent = stats.n50 ? formatSizeWithUnit(stats.n50) : '-';
    elements.statsGC.textContent = stats.gc_content ? `${stats.gc_content}%` : '-';
    elements.statsLongest.textContent = stats.longest_scaffold ? formatSizeWithUnit(stats.longest_scaffold) : '-';
    
    // Modo e versão
    if (stats.command_line) {
        // Tentar extrair modo do comando
        const modeMatch = stats.command_line.match(/--([a-z]+)/);
        if (modeMatch) {
            elements.statsMode.textContent = modeMatch[1];
        } else {
            elements.statsMode.textContent = 'isolate (padrão)';
        }
        
        // Salvar comando para o modal
        resultsState.command = stats.command_line;
    } else {
        elements.statsMode.textContent = '-';
    }
    
    elements.statsVersion.textContent = stats.spades_version || '-';
    
    // Mostrar detalhes
    elements.assemblyDetailsPlaceholder.classList.add('d-none');
    elements.assemblyDetails.classList.remove('d-none');
}

// Mostrar modal com o comando SPAdes
function showCommandModal() {
    if (resultsState.command) {
        elements.spadesCommand.textContent = resultsState.command;
        elements.cmdModal.show();
    } else {
        showToast('Aviso', 'Comando SPAdes não disponível', 'warning');
    }
}

// Criar e baixar relatório da montagem
function downloadReport() {
    if (!resultsState.selectedResult) {
        showToast('Aviso', 'Selecione uma montagem primeiro', 'warning');
        return;
    }
    
    // Encontrar o resultado
    const result = resultsState.results.find(r => r.name === resultsState.selectedResult);
    
    if (!result || !result.stats) {
        showToast('Aviso', 'Estatísticas não disponíveis para esta montagem', 'warning');
        return;
    }
    
    try {
        const stats = result.stats;
        
        // Criar texto do relatório
        let reportText = `# Relatório de Montagem: ${resultsState.selectedResult}\n\n`;
        reportText += `Data: ${new Date().toLocaleString()}\n\n`;
        
        reportText += `## Estatísticas Gerais\n\n`;
        reportText += `- Número de contigs: ${stats.scaffold_count || 'N/A'}\n`;
        reportText += `- Tamanho total: ${stats.total_length ? formatSizeWithUnit(stats.total_length) : 'N/A'}\n`;
        reportText += `- N50: ${stats.n50 ? formatSizeWithUnit(stats.n50) : 'N/A'}\n`;
        reportText += `- Contig mais longo: ${stats.longest_scaffold ? formatSizeWithUnit(stats.longest_scaffold) : 'N/A'}\n`;
        reportText += `- Conteúdo GC: ${stats.gc_content ? `${stats.gc_content}%` : 'N/A'}\n\n`;
        
        reportText += `## Informações do SPAdes\n\n`;
        reportText += `- Versão do SPAdes: ${stats.spades_version || 'N/A'}\n`;
        reportText += `- Comando utilizado: ${stats.command_line || 'N/A'}\n\n`;
        
        reportText += `## Arquivos Disponíveis\n\n`;
        
        // Listar arquivos principais
        const mainFiles = [
            'scaffolds.fasta', 
            'contigs.fasta', 
            'assembly_graph.fastg', 
            'spades.log'
        ];
        
        mainFiles.forEach(filename => {
            const file = resultsState.files.find(f => f.name === filename);
            if (file) {
                reportText += `- ${file.name} (${formatFileSize(file.size)})\n`;
            }
        });
        
        // Criar blob e link para download
        const blob = new Blob([reportText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        
        // Criar link temporário e clicar nele
        const a = document.createElement('a');
        a.href = url;
        a.download = `assembly_report_${resultsState.selectedResult}.txt`;
        document.body.appendChild(a);
        a.click();
        
        // Limpar
        setTimeout(() => {
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }, 100);
        
        showToast('Sucesso', 'Relatório baixado com sucesso', 'success');
    } catch (error) {
        console.error('Erro ao criar relatório:', error);
        showToast('Erro', 'Não foi possível criar o relatório', 'danger');
    }
}

// Baixar arquivo visualizado
function downloadViewedFile() {
    // O link já foi configurado na função viewFile, então não precisamos fazer nada aqui
}

// Baixar todos os arquivos como ZIP
function downloadAllFiles() {
    if (!resultsState.selectedResult) {
        showToast('Aviso', 'Selecione uma montagem primeiro', 'warning');
        return;
    }
    
    // Como não podemos criar um ZIP no navegador facilmente,
    // vamos explicar que isso deve ser feito no servidor
    
    createDownloadZip(resultsState.selectedResult);
}

// Criar e baixar ZIP dos resultados
function createDownloadZip(resultName) {
    // Redirecionar para endpoint de download
    window.location.href = `/api/results/zip/${resultName}`;
    
    showToast('Download', 'Iniciando download dos arquivos...', 'info');
}

// Confirmar exclusão de montagem
function confirmDeleteAssembly(resultName = null) {
    // Se não for especificado, usar o selecionado atualmente
    if (!resultName) {
        resultName = resultsState.selectedResult;
    }
    
    if (!resultName) {
        showToast('Aviso', 'Selecione uma montagem primeiro', 'warning');
        return;
    }
    
    // Configurar modal
    elements.deleteAssemblyName.textContent = resultName;
    resultsState.deleteTarget = resultName;
    
    // Mostrar modal
    elements.deleteModal.show();
}

// Excluir montagem
async function deleteAssembly() {
    const resultName = resultsState.deleteTarget;
    
    if (!resultName) {
        return;
    }
    
    try {
        // Atualizar UI
        elements.btnConfirmDelete.disabled = true;
        elements.btnConfirmDelete.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Excluindo...';
        
        // Enviar requisição
        const response = await fetchWithErrorHandling(`/api/results/delete/${resultName}`, {
            method: 'DELETE'
        });
        
        if (response.status === 'success') {
            // Fechar modal
            elements.deleteModal.hide();
            
            // Resetar seleção se era o resultado selecionado
            if (resultsState.selectedResult === resultName) {
                resultsState.selectedResult = null;
                elements.filesPlaceholder.innerHTML = `
                    <div class="text-center py-5">
                        <i class="fas fa-file-code fa-3x text-muted mb-3"></i>
                        <p class="lead text-muted">Selecione uma montagem para ver os arquivos</p>
                    </div>
                `;
                elements.filesPlaceholder.classList.remove('d-none');
                elements.filesList.classList.add('d-none');
                
                elements.assemblyDetailsPlaceholder.innerHTML = `
                    <div class="text-center py-5">
                        <i class="fas fa-chart-pie fa-3x text-muted mb-3"></i>
                        <p class="lead text-muted">Selecione uma montagem para ver os detalhes</p>
                    </div>
                `;
                elements.assemblyDetailsPlaceholder.classList.remove('d-none');
                elements.assemblyDetails.classList.add('d-none');
                
                // Desabilitar botões
                elements.btnDownloadAllFiles.disabled = true;
                elements.btnDeleteAssembly.disabled = true;
            }
            
            // Atualizar lista de resultados
            await loadResults();
            
            showToast('Sucesso', `Montagem ${resultName} excluída com sucesso`, 'success');
        } else {
            throw new Error(response.message || 'Erro ao excluir montagem');
        }
    } catch (error) {
        showToast('Erro', error.message, 'danger');
    } finally {
        // Resetar UI
        elements.btnConfirmDelete.disabled = false;
        elements.btnConfirmDelete.innerHTML = '<i class="fas fa-trash-alt me-1"></i> Excluir Permanentemente';
        
        // Limpar alvo de exclusão
        resultsState.deleteTarget = null;
    }
}

// Exibir loading na tabela
function showLoadingInTable() {
    elements.resultsTableBody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center">
                <div class="spinner-border text-primary my-3" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
                <p>Carregando resultados de montagem...</p>
            </td>
        </tr>
    `;
}

// Exibir erro na tabela
function showErrorInTable(message) {
    elements.resultsTableBody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center">
                <div class="alert alert-danger my-3">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                </div>
                <button class="btn btn-primary btn-sm" onclick="loadResults()">
                    <i class="fas fa-sync me-1"></i> Tentar Novamente
                </button>
            </td>
        </tr>
    `;
}

// Formatar tamanho com unidade
function formatSizeWithUnit(bytes) {
    if (bytes < 1000) {
        return `${bytes} bp`;
    } else if (bytes < 1000000) {
        return `${(bytes / 1000).toFixed(1)} Kbp`;
    } else if (bytes < 1000000000) {
        return `${(bytes / 1000000).toFixed(2)} Mbp`;
    } else {
        return `${(bytes / 1000000000).toFixed(2)} Gbp`;
    }
}

// Expor funções necessárias para HTML
window.loadResults = loadResults;
window.selectResult = selectResult;
window.analyzeAssembly = analyzeAssembly;