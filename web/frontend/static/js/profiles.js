// Profiles management 
/**
 * SPAdes Master Web - Perfis de Servidor
 * Gerencia os perfis de conexão SSH para servidores remotos
 */

// Remove socket initialization since it's already done in base.html
// const socket = io();

// Estado da página
const profilesState = {
    profiles: [],
    editing: null,
    currentProfile: null,
    testing: false
};

// Elementos da interface
const elements = {
    profilesTableBody: document.getElementById('profiles-table-body'),
    btnAddProfile: document.getElementById('btn-add-profile'),
    profileModal: new bootstrap.Modal(document.getElementById('profileModal')),
    profileForm: document.getElementById('profile-form'),
    profileId: document.getElementById('profile-id'),
    profileName: document.getElementById('profile-name'),
    profileHost: document.getElementById('profile-host'),
    profilePort: document.getElementById('profile-port'),
    profileUsername: document.getElementById('profile-username'),
    profilePassword: document.getElementById('profile-password'),
    authPassword: document.getElementById('auth-password'),
    authKey: document.getElementById('auth-key'),
    passwordSection: document.getElementById('password-section'),
    keySection: document.getElementById('key-section'),
    profileKeyPath: document.getElementById('profile-key-path'),
    btnBrowseKey: document.getElementById('btn-browse-key'),
    btnTestConnection: document.getElementById('btn-test-connection'),
    btnSaveProfile: document.getElementById('btn-save-profile'),
    confirmModal: new bootstrap.Modal(document.getElementById('confirmModal')),
    confirmProfileName: document.getElementById('confirm-profile-name'),
    btnConfirmDelete: document.getElementById('btn-confirm-delete'),
    serverInfoModal: new bootstrap.Modal(document.getElementById('serverInfoModal')),
    serverCpu: document.getElementById('server-cpu'),
    serverMemory: document.getElementById('server-memory'),
    serverFreeMemory: document.getElementById('server-free-memory'),
    serverDisk: document.getElementById('server-disk'),
    spadesStatusContainer: document.getElementById('spades-status-container'),
    spadesPathContainer: document.getElementById('spades-path-container'),
    spadesPath: document.getElementById('spades-path'),
    btnCopyPath: document.getElementById('btn-copy-path')
};

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    // Verificar se o socket está disponível
    if (typeof socket === 'undefined') {
        showErrorInTable('Erro de conexão com o servidor. Recarregue a página.');
        return;
    }

    // Carregar perfis
    loadProfiles();
    
    // Configurar event listeners
    setupEventListeners();
    
    // Configurar socket listeners
    setupSocketListeners();
});

// Carregar perfis de servidor
async function loadProfiles() {
    try {
        showLoadingInTable();
        
        const response = await fetch('/api/profiles/');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.status === 'success' && Array.isArray(data.profiles)) {
            profilesState.profiles = data.profiles;
            renderProfilesTable();
        } else {
            throw new Error(data.message || 'Invalid response format');
        }
    } catch (error) {
        console.error('Erro ao carregar perfis:', error);
        showErrorInTable('Não foi possível carregar perfis. Tente recarregar a página.');
    }
}

// Mostrar mensagem de erro na tabela
function showErrorInTable(message) {
    if (elements.profilesTableBody) {
        elements.profilesTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-danger">
                    <i class="fas fa-exclamation-circle me-2"></i>
                    ${message}
                </td>
            </tr>
        `;
    }
}

// Mostrar loading na tabela
function showLoadingInTable() {
    if (elements.profilesTableBody) {
        elements.profilesTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Carregando...</span>
                    </div>
                </td>
            </tr>
        `;
    }
}

// Configurar event listeners
function setupEventListeners() {
    // Botão adicionar perfil
    elements.btnAddProfile.addEventListener('click', () => showProfileModal());
    
    // Formulário de perfil
    elements.authPassword.addEventListener('change', toggleAuthMethod);
    elements.authKey.addEventListener('change', toggleAuthMethod);
    elements.btnBrowseKey.addEventListener('click', browseKeyFile);
    elements.btnTestConnection.addEventListener('click', testConnection);
    elements.btnSaveProfile.addEventListener('click', saveProfile);
    
    // Botão de confirmação de exclusão
    elements.btnConfirmDelete.addEventListener('click', deleteProfile);
    
    // Botão copiar caminho do SPAdes
    elements.btnCopyPath.addEventListener('click', () => copyToClipboard(elements.spadesPath.value));
}

// Configurar socket listeners
function setupSocketListeners() {
    socket.on('connect_result', (data) => {
        if (profilesState.testing) {
            profilesState.testing = false;
            
            // Atualizar UI de teste
            elements.btnTestConnection.disabled = false;
            elements.btnTestConnection.innerHTML = '<i class="fas fa-plug me-1"></i> Testar Conexão';
            
            // Atualizar status do perfil na tabela
            const statusCell = document.querySelector(`tr button[data-profile="${profilesState.currentProfile}"]`)
                .closest('tr')
                .querySelector('.profile-status');
            
            if (statusCell) {
                if (data.success) {
                    statusCell.innerHTML = '<span class="badge bg-success">Conectado</span>';
                    // Mostrar modal com detalhes do servidor
                    showServerInfoModal(data);
                    showToast('Sucesso', 'Conexão estabelecida com sucesso', 'success');
                } else {
                    statusCell.innerHTML = '<span class="badge bg-danger">Falha</span>';
                    showToast('Erro', data.message || 'Falha na conexão com o servidor', 'danger');
                }
            }
        }
    });

    // Adicionar listener para desconexão
    socket.on('disconnect', () => {
        if (profilesState.testing) {
            profilesState.testing = false;
            elements.btnTestConnection.disabled = false;
            elements.btnTestConnection.innerHTML = '<i class="fas fa-plug me-1"></i> Testar Conexão';
            showToast('Erro', 'Conexão com o servidor perdida', 'danger');
        }
    });

    // Adicionar listener para erros de conexão
    socket.on('connect_error', (error) => {
        if (profilesState.testing) {
            profilesState.testing = false;
            elements.btnTestConnection.disabled = false;
            elements.btnTestConnection.innerHTML = '<i class="fas fa-plug me-1"></i> Testar Conexão';
            showToast('Erro', 'Erro ao conectar com o servidor: ' + error.message, 'danger');
        }
    });
}

// Renderizar tabela de perfis
function renderProfilesTable() {
    const tableBody = elements.profilesTableBody;
    tableBody.innerHTML = '';
    
    if (profilesState.profiles.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">
                    <p class="my-3 text-muted">Nenhum perfil de servidor cadastrado.</p>
                    <button class="btn btn-primary btn-sm" onclick="showProfileModal()">
                        <i class="fas fa-plus me-1"></i> Adicionar Perfil
                    </button>
                </td>
            </tr>
        `;
        return;
    }
    
    // Adicionar cada perfil à tabela
    profilesState.profiles.forEach(profileName => {
        const row = document.createElement('tr');
        
        // Células da tabela
        row.innerHTML = `
            <td>${profileName}</td>
            <td class="profile-host">Carregando...</td>
            <td class="profile-username">Carregando...</td>
            <td class="profile-auth">Carregando...</td>
            <td class="profile-status">
                <span class="badge bg-secondary">Não testado</span>
            </td>
            <td>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary btn-test" data-profile="${profileName}" title="Testar Conexão">
                        <i class="fas fa-plug"></i>
                    </button>
                    <button class="btn btn-outline-secondary btn-edit" data-profile="${profileName}" title="Editar">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn btn-outline-danger btn-delete" data-profile="${profileName}" title="Excluir">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        
        // Adicionar a linha à tabela
        tableBody.appendChild(row);
        
        // Carregar detalhes do perfil
        loadProfileDetails(profileName, row);
    });
    
    // Adicionar event listeners para os botões
    addTableButtonListeners();
}

// Carregar detalhes do perfil
async function loadProfileDetails(profileName, row) {
    try {
        const response = await fetch(`/api/profiles/${profileName}`);
        const data = await response.json();
        
        if (data.status === 'success' && data.profile) {
            const profile = data.profile;
            
            // Atualizar células da tabela
            row.querySelector('.profile-host').textContent = `${profile.host}${profile.port ? `:${profile.port}` : ''}`;
            row.querySelector('.profile-username').textContent = profile.username;
            
            const authMethod = profile.use_key ? 
                '<span class="badge bg-info">Chave SSH</span>' : 
                '<span class="badge bg-warning">Senha</span>';
            row.querySelector('.profile-auth').innerHTML = authMethod;
        } else {
            throw new Error('Invalid response format');
        }
    } catch (error) {
        console.error(`Erro ao carregar detalhes do perfil ${profileName}:`, error);
        row.querySelector('.profile-host').textContent = 'Erro ao carregar';
        row.querySelector('.profile-username').textContent = 'Erro ao carregar';
        row.querySelector('.profile-auth').textContent = 'Erro ao carregar';
    }
}

// Adicionar event listeners para os botões da tabela
function addTableButtonListeners() {
    // Botões de teste
    document.querySelectorAll('.btn-test').forEach(button => {
        button.addEventListener('click', () => {
            const profileName = button.dataset.profile;
            testProfileConnection(profileName, button);
        });
    });
    
    // Botões de edição
    document.querySelectorAll('.btn-edit').forEach(button => {
        button.addEventListener('click', () => {
            const profileName = button.dataset.profile;
            showProfileModal(profileName);
        });
    });
    
    // Botões de exclusão
    document.querySelectorAll('.btn-delete').forEach(button => {
        button.addEventListener('click', () => {
            const profileName = button.dataset.profile;
            confirmDeleteProfile(profileName);
        });
    });
}

// Teste de conexão para um perfil específico
async function testProfileConnection(profileName, button) {
    profilesState.currentProfile = profileName;
    profilesState.testing = true;
    
    try {
        // Atualizar UI
        button.disabled = true;
        button.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>';
        
        // Encontrar célula de status
        const statusCell = button.closest('tr').querySelector('.profile-status');
        statusCell.innerHTML = `
            <span class="badge bg-warning">
                <span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span>
                Testando...
            </span>
        `;
        
        // Enviar requisição para testar conexão
        const response = await fetch(`/api/profiles/${profileName}/test`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            // O resultado virá via WebSocket
            showToast('Testando', `Testando conexão com ${profileName}...`, 'info');
        } else {
            throw new Error(data.message || 'Falha ao iniciar teste de conexão');
        }
    } catch (error) {
        profilesState.testing = false;
        showToast('Erro', error.message, 'danger');
        
        // Resetar UI
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-plug"></i>';
        
        // Atualizar status
        const statusCell = button.closest('tr').querySelector('.profile-status');
        statusCell.innerHTML = '<span class="badge bg-danger">Falha</span>';
    }
}

// Mostrar modal com informações do servidor
function showServerInfoModal(data) {
    // Limpar e atualizar informações do modal
    elements.serverCpu.textContent = '-';
    elements.serverMemory.textContent = '-';
    elements.serverFreeMemory.textContent = '-';
    elements.serverDisk.textContent = '-';
    
    elements.spadesStatusContainer.innerHTML = `
        <div class="alert alert-secondary">
            <i class="fas fa-spinner fa-spin me-2"></i>
            Verificando SPAdes...
        </div>
    `;
    
    elements.spadesPathContainer.style.display = 'none';
    
    // Preencher com informações do servidor, se disponíveis
    if (data.resources) {
        elements.serverCpu.textContent = data.resources.cpu_count;
        
        if (typeof data.resources.total_mem === 'number') {
            const memGB = (data.resources.total_mem / 1024).toFixed(1);
            elements.serverMemory.textContent = `${data.resources.total_mem} MB (${memGB} GB)`;
        } else {
            elements.serverMemory.textContent = data.resources.total_mem;
        }
        
        if (typeof data.resources.free_mem === 'number') {
            const freeGB = (data.resources.free_mem / 1024).toFixed(1);
            elements.serverFreeMemory.textContent = `${data.resources.free_mem} MB (${freeGB} GB)`;
        } else {
            elements.serverFreeMemory.textContent = data.resources.free_mem;
        }
        
        elements.serverDisk.textContent = data.resources.disk_avail;
    }
    
    // Mostrar status do SPAdes
    if (data.spades_path) {
        elements.spadesStatusContainer.innerHTML = `
            <div class="alert alert-success">
                <i class="fas fa-check-circle me-2"></i>
                SPAdes encontrado e pronto para uso
            </div>
        `;
        
        elements.spadesPathContainer.style.display = 'flex';
        elements.spadesPath.value = data.spades_path;
    } else {
        elements.spadesStatusContainer.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-times-circle me-2"></i>
                SPAdes não encontrado no servidor
            </div>
        `;
    }
    
    // Mostrar modal
    elements.serverInfoModal.show();
    
    // Resetar botão
    const button = document.querySelector(`tr button[data-profile="${profilesState.currentProfile}"]`);
    if (button) {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-plug"></i>';
    }
    
    // Limpar estado
    profilesState.currentProfile = null;
}

// Mostrar modal de perfil para adicionar ou editar
function showProfileModal(profileName = null) {
    // Limpar formulário
    elements.profileForm.reset();
    elements.profileId.value = '';
    elements.profileName.disabled = false;
    
    // Título do modal
    const modalTitle = document.getElementById('profileModalLabel');
    modalTitle.textContent = profileName ? `Editar Perfil: ${profileName}` : 'Adicionar Novo Perfil';
    
    // Se for edição, carregar dados do perfil
    if (profileName) {
        elements.profileId.value = profileName;
        elements.profileName.value = profileName;
        elements.profileName.disabled = true;
        
        // Marcar para carregar detalhes após modal abrir
        profilesState.editing = profileName;
    } else {
        profilesState.editing = null;
    }
    
    // Configurar método de autenticação inicial
    toggleAuthMethod();
    
    // Abrir modal
    elements.profileModal.show();
    
    // Se estivermos editando, carregar detalhes do perfil
    if (profilesState.editing) {
        loadProfileFormData(profilesState.editing);
    }
}

// Carregar dados de um perfil para o formulário
async function loadProfileFormData(profileName) {
    try {
        const response = await fetch(`/api/profiles/${profileName}`);
        const data = await response.json();
        
        if (data.status === 'success' && data.profile) {
            const profile = data.profile;
            
            // Preencher campos
            elements.profileHost.value = profile.host;
            elements.profilePort.value = profile.port || '';
            elements.profileUsername.value = profile.username;
            
            // Método de autenticação
            if (profile.use_key) {
                elements.authKey.checked = true;
                elements.profileKeyPath.value = profile.key_path;
            } else {
                elements.authPassword.checked = true;
                elements.profilePassword.value = ''; // Por segurança, não exibimos a senha existente
            }
            
            // Atualizar interface com base no método de autenticação
            toggleAuthMethod();
        }
    } catch (error) {
        console.error(`Erro ao carregar dados do perfil ${profileName}:`, error);
        showToast('Erro', `Não foi possível carregar os dados do perfil ${profileName}`, 'danger');
    }
}

// Alternar método de autenticação
function toggleAuthMethod() {
    const useKey = elements.authKey.checked;
    
    if (useKey) {
        elements.passwordSection.style.display = 'none';
        elements.keySection.style.display = 'block';
        elements.profilePassword.required = false;
        elements.profileKeyPath.required = true;
    } else {
        elements.passwordSection.style.display = 'block';
        elements.keySection.style.display = 'none';
        elements.profilePassword.required = true;
        elements.profileKeyPath.required = false;
    }
}

// Abrir diálogo para selecionar arquivo de chave SSH
function browseKeyFile() {
    // Mostrar uma mensagem informativa
    showToast('Seleção de Arquivo', 'Escolha o arquivo de chave SSH no seu sistema de arquivos', 'info');
    
    // Como não podemos acessar o sistema de arquivos diretamente via JavaScript,
    // esta função apenas exibe uma mensagem de instrução com alternativas
    alert(`Para selecionar a chave SSH:
    
1. Anote o caminho completo do arquivo de chave no seu sistema
2. Cole o caminho no campo "Caminho da Chave SSH"

Exemplos de caminhos:
- Windows: C:\\Users\\SeuUsuario\\.ssh\\id_rsa
- Mac/Linux: /home/seuusuario/.ssh/id_rsa

Observação: Você precisará selecionar a chave novamente a cada execução do aplicativo.`);
}

// Testar conexão
async function testConnection() {
    // Validar formulário
    if (!validateProfileForm()) {
        return;
    }
    
    try {
        // Obter dados do formulário
        const profileData = getProfileFormData();
        
        // Enviar requisição para testar conexão
        const response = await fetch(`/api/profiles/${profileData.name}/test`, {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            // O resultado virá via WebSocket
            showToast('Testando', `Testando conexão com ${profileData.name}...`, 'info');
        } else {
            throw new Error(data.message || 'Falha ao iniciar teste de conexão');
        }
    } catch (error) {
        showToast('Erro', error.message, 'danger');
    }
}

// Salvar perfil
async function saveProfile() {
    // Validar formulário
    if (!validateProfileForm()) {
        return;
    }
    
    try {
        // Obter dados do formulário
        const profileData = getProfileFormData();
        
        // Determinar se é adição ou atualização
        const isUpdate = !!elements.profileId.value;
        const url = isUpdate ? `/api/profiles/${profileData.name}` : '/api/profiles/';
        const method = isUpdate ? 'PUT' : 'POST';
        
        // Enviar requisição
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(profileData)
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast('Sucesso', data.message, 'success');
            elements.profileModal.hide();
            loadProfiles();
        } else {
            throw new Error(data.message || 'Falha ao salvar perfil');
        }
    } catch (error) {
        showToast('Erro', error.message, 'danger');
    }
}

// Confirmar exclusão de perfil
function confirmDeleteProfile(profileName) {
    elements.confirmProfileName.textContent = profileName;
    profilesState.editing = profileName;
    elements.confirmModal.show();
}

// Excluir perfil
async function deleteProfile() {
    const profileName = profilesState.editing;
    
    try {
        const response = await fetch(`/api/profiles/${profileName}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            showToast('Sucesso', data.message, 'success');
            elements.confirmModal.hide();
            loadProfiles();
        } else {
            throw new Error(data.message || 'Falha ao excluir perfil');
        }
    } catch (error) {
        showToast('Erro', error.message, 'danger');
    } finally {
        profilesState.editing = null;
    }
}

// Validar formulário de perfil
function validateProfileForm() {
    const form = elements.profileForm;
    
    if (!form.checkValidity()) {
        form.reportValidity();
        return false;
    }
    
    return true;
}

// Obter dados do formulário de perfil
function getProfileFormData() {
    return {
        name: elements.profileName.value.trim(),
        host: elements.profileHost.value.trim(),
        port: elements.profilePort.value.trim(),
        username: elements.profileUsername.value.trim(),
        password: elements.profilePassword.value,
        key_path: elements.profileKeyPath.value.trim(),
        use_key: elements.authKey.checked
    };
}

// Mostrar loading na tabela
function showLoadingInTable() {
    elements.profilesTableBody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Carregando...</span>
                </div>
            </td>
        </tr>
    `;
}

// Mostrar erro na tabela
function showErrorInTable(message) {
    elements.profilesTableBody.innerHTML = `
        <tr>
            <td colspan="6" class="text-center">
                <div class="alert alert-danger mb-0">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    ${message}
                </div>
            </td>
        </tr>
    `;
}

// Copiar texto para a área de transferência
function copyToClipboard(text) {
    navigator.clipboard.writeText(text)
        .then(() => showToast('Sucesso', 'Texto copiado para a área de transferência', 'success'))
        .catch(() => showToast('Erro', 'Não foi possível copiar o texto', 'danger'));
}

// Mostrar toast de notificação
function showToast(title, message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <strong>${title}</strong><br>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast, {
        animation: true,
        autohide: true,
        delay: 5000
    });
    
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        document.body.removeChild(toast);
    });
}