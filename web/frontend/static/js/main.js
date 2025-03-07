// Main JavaScript file 
/**
 * SPAdes Master Web - JavaScript principal
 * Funções comuns compartilhadas em toda a aplicação
 */

// Inicialização do Socket.IO
const socket = io('/logs');

// Estado global da aplicação
const appState = {
    connected: false,
    serverInfo: null,
    currentProfile: null,
    jobRunning: false
};

// Manejadores de eventos do Socket.IO
socket.on('connect', () => {
    console.log('Conectado ao servidor de WebSocket');
    
    // Atualizar indicador de conexão do Socket
    const apiStatus = document.getElementById('api-status');
    if (apiStatus) {
        apiStatus.textContent = 'Online';
        apiStatus.classList.remove('bg-secondary', 'bg-danger');
        apiStatus.classList.add('bg-success');
    }
    
    const socketStatus = document.getElementById('socket-status');
    if (socketStatus) {
        socketStatus.textContent = 'Conectado';
        socketStatus.classList.remove('bg-secondary', 'bg-danger');
        socketStatus.classList.add('bg-success');
    }
});

socket.on('disconnect', () => {
    console.log('Desconectado do servidor de WebSocket');
    
    // Atualizar indicador de conexão do Socket
    const socketStatus = document.getElementById('socket-status');
    if (socketStatus) {
        socketStatus.textContent = 'Desconectado';
        socketStatus.classList.remove('bg-secondary', 'bg-success');
        socketStatus.classList.add('bg-danger');
    }
});

socket.on('status_update', (data) => {
    console.log('Status update:', data.message);
    // Atualizar status na interface, se houver um elemento para isso
});

socket.on('log_message', (data) => {
    // Adicionar mensagem ao log se existir um container de log
    const logContent = document.getElementById('log-content');
    if (logContent) {
        addLogMessage(data);
    }
});

socket.on('connect_result', (data) => {
    // Atualizar estado da conexão
    appState.connected = data.success;
    
    // Atualizar indicador de conexão
    updateConnectionIndicator(data.success);
    
    // Se conectado com sucesso, armazenar informações do servidor
    if (data.success && data.resources) {
        appState.serverInfo = data.resources;
        appState.serverInfo.spades_path = data.spades_path || null;
    }
    
    // Disparar evento personalizado para que as páginas possam reagir
    const event = new CustomEvent('serverConnection', { 
        detail: { 
            success: data.success,
            message: data.message,
            resources: data.resources,
            spades_path: data.spades_path
        } 
    });
    document.dispatchEvent(event);
});

// Função para adicionar mensagem no log
function addLogMessage(data) {
    const logContent = document.getElementById('log-content');
    if (!logContent) return;
    
    // Criar contêiner para a entrada de log
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    
    // Extrair timestamp da mensagem formatada ou usar atual
    let timestamp = '';
    const timestampMatch = data.message.match(/^\[(.*?)\]/);
    if (timestampMatch && timestampMatch[1]) {
        timestamp = timestampMatch[1];
    } else {
        const now = new Date();
        timestamp = now.toISOString().replace('T', ' ').substr(0, 19);
    }
    
    // Criar span para timestamp
    const timeSpan = document.createElement('span');
    timeSpan.className = 'log-timestamp';
    timeSpan.textContent = timestamp;
    
    // Criar span para nível
    const levelSpan = document.createElement('span');
    levelSpan.className = 'log-level ' + data.level;
    levelSpan.textContent = data.level;
    
    // Obter a mensagem sem timestamp e nível
    let messageText = data.raw_message || data.message;
    if (data.message.includes('] [')) {
        messageText = data.message.replace(/^\[.*?\] \[.*?\] /, '');
    }
    
    // Criar span para mensagem
    const messageSpan = document.createElement('span');
    messageSpan.className = 'log-message';
    messageSpan.textContent = messageText;
    
    // Adicionar componentes à entrada de log
    logEntry.appendChild(timeSpan);
    logEntry.appendChild(levelSpan);
    logEntry.appendChild(messageSpan);
    
    // Adicionar ao container de log
    logContent.appendChild(logEntry);
    
    // Rolar para o final
    logContent.parentElement.scrollTop = logContent.parentElement.scrollHeight;
}

// Função para atualizar indicador de conexão
function updateConnectionIndicator(connected) {
    const indicator = document.getElementById('connection-indicator');
    if (!indicator) return;
    
    if (connected) {
        indicator.className = 'text-white badge bg-success';
        indicator.innerHTML = '<i class="fas fa-plug"></i> Conectado';
    } else {
        indicator.className = 'text-white badge bg-danger';
        indicator.innerHTML = '<i class="fas fa-plug"></i> Desconectado';
    }
    
    // Também atualizar no dashboard, se existir
    const sshStatus = document.getElementById('ssh-status');
    if (sshStatus) {
        if (connected) {
            sshStatus.textContent = 'Conectado';
            sshStatus.classList.remove('bg-danger');
            sshStatus.classList.add('bg-success');
        } else {
            sshStatus.textContent = 'Desconectado';
            sshStatus.classList.remove('bg-success');
            sshStatus.classList.add('bg-danger');
        }
    }
}

// Ajuda para formatação de números
function formatNumber(num) {
    return new Intl.NumberFormat().format(num);
}

// Formatar tamanho de arquivo
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Formatar duração
function formatDuration(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    return [
        hours.toString().padStart(2, '0'),
        minutes.toString().padStart(2, '0'),
        secs.toString().padStart(2, '0')
    ].join(':');
}

// Função de utilidade para requisições fetch
async function fetchWithErrorHandling(url, options = {}) {
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ 
                message: `Erro HTTP: ${response.status}` 
            }));
            
            throw new Error(errorData.message || `Erro HTTP: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('Erro na requisição:', error);
        
        // Exibir alerta de erro se não for uma requisição silenciosa
        if (!options.silent) {
            showToast('Erro', error.message, 'danger');
        }
        
        throw error;
    }
}

// Exibir toast para mensagens
function showToast(title, message, type = 'info') {
    // Verificar se o elemento toast-container existe
    let toastContainer = document.getElementById('toast-container');
    
    // Se não existir, criar
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    // Criar ID único para o toast
    const toastId = 'toast-' + Date.now();
    
    // Criar elemento de toast
    const toastHtml = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type} text-white">
                <i class="fas fa-info-circle me-2"></i>
                <strong class="me-auto">${title}</strong>
                <small>Agora</small>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Fechar"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    // Adicionar ao container
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    // Inicializar e mostrar o toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();
    
    // Remover após fechar
    toastElement.addEventListener('hidden.bs.toast', () => {
        toastElement.remove();
    });
}

// Função para copiar texto para a área de transferência
function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
        .then(() => {
            showToast('Sucesso', 'Texto copiado para a área de transferência', 'success');
        })
        .catch(err => {
            console.error('Erro ao copiar texto: ', err);
            showToast('Erro', 'Não foi possível copiar o texto', 'danger');
        });
}

// Verificar o status da API quando a página carregar
document.addEventListener('DOMContentLoaded', async () => {
    // Verificar status da API
    try {
        const apiStatus = document.getElementById('api-status');
        if (apiStatus) {
            // Tentar acessar endpoint de status
            const response = await fetch('/api/status');
            const data = await response.json();
            
            if (data.status === 'online') {
                apiStatus.textContent = 'Online';
                apiStatus.classList.remove('bg-secondary');
                apiStatus.classList.add('bg-success');
            } else {
                throw new Error('API indisponível');
            }
        }
    } catch (error) {
        console.error('Erro ao verificar status da API:', error);
        const apiStatus = document.getElementById('api-status');
        if (apiStatus) {
            apiStatus.textContent = 'Offline';
            apiStatus.classList.remove('bg-secondary');
            apiStatus.classList.add('bg-danger');
        }
    }
});