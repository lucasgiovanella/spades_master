#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import platform
import os
import threading
from datetime import datetime

try:
    from ttkthemes import ThemedTk
    HAS_TTKTHEMES = True
except ImportError:
    HAS_TTKTHEMES = False

if HAS_TTKTHEMES:
    BaseClass = ThemedTk
else:
    BaseClass = tk.Tk

from config.settings import APP_VERSION, APP_NAME
from utils.status_updater import StatusUpdater
from utils.logging_utils import log_info, log_error
from utils.ssh_utils import open_ssh_terminal
from models.server_profile import ServerProfile
from services.job_manager import JobManager
from ui.frames.config_frame import ConfigFrame
from ui.frames.execution_frame import ExecutionFrame  # Agora esse arquivo contém o UnifiedExecutionFrame
from ui.frames.results_frame import ResultsFrame
from ui.dialogs.profile_dialog import ProfileManagerDialog
from ui.dialogs.params_dialog import SPAdesParamsDialog
from ui.dialogs.spades_path_dialog import SpadesPathDialog


class SPAdesMasterApp(BaseClass):
    """Aplicativo principal para gerenciamento de montagens SPAdes"""
    def __init__(self):
        
        # Inicializar a classe pai apenas uma vez, com base na disponibilidade do ttkthemes
        if HAS_TTKTHEMES:
            super().__init__()  # Inicializa ThemedTk
            # self.set_theme("equilux")
        else:
            super().__init__()  # Inicializa Tk padrão
        
        # Configurar a janela principal
        self.title(f"{APP_NAME} v{APP_VERSION} - Gerenciador de Montagens")
        
        # Criar ícone se disponível
        try:
            # Tentar carregar ícone se disponível
            if platform.system() == "Windows":
                icon_path = "resources/spades_icon.ico"
                if os.path.exists(icon_path):
                    self.iconbitmap(icon_path)
        except Exception:
            pass
            
        # Variáveis
        self.status_var = tk.StringVar(value="Pronto")
        self.progress_var = tk.IntVar(value=0)
        
        # Criar componentes da interface
        self._create_menu()
        self._create_widgets()
        
        # Instanciar status_updater sem o log_text duplicado
        self.status_updater = StatusUpdater(self.status_var, None, self.progress_var)
        self.status_updater.start()
        
        # Instanciar modelos e serviços
        self.server_profiles = ServerProfile()
        self.job_manager = JobManager(self.status_updater)
        
        # Configurar frames específicos
        self._setup_frames()
        
        # Vincular eventos
        self._bind_events()
        
        # Inicialização
        self.status_updater.update_log(f"Aplicativo {APP_NAME} v{APP_VERSION} iniciado")
        
        # Configurar encerramento correto
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        
    def _on_close(self):
        """Função chamada ao fechar a aplicação"""
        try:
            # Perguntar se deve cancelar o job em execução
            if self.job_manager.job_running:
                if messagebox.askyesno("Job em Execução", "Há um job em execução. Deseja cancelá-lo antes de sair?"):
                    self.job_manager.cancel_job()
                    
            # Desconectar do servidor
            if self.job_manager.connected:
                self.job_manager.disconnect()
                
            # Parar o processamento de log
            if hasattr(self, 'status_updater'):
                self.status_updater.stop()
                
        except Exception as e:
            log_error(f"Erro ao fechar aplicação: {str(e)}")
            
        # Fechar a aplicação
        self.destroy()
        
    def _create_menu(self):
        """Cria o menu principal da aplicação"""
        menubar = tk.Menu(self)
        
        # Menu Arquivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Salvar Log", command=self._save_log)
        file_menu.add_separator()
        file_menu.add_command(label="Sair", command=self._on_close)
        menubar.add_cascade(label="Arquivo", menu=file_menu)
        
        # Menu Servidor
        server_menu = tk.Menu(menubar, tearoff=0)
        server_menu.add_command(label="Gerenciar Perfis", command=self._show_profile_manager)
        server_menu.add_command(label="Testar Conexão", command=self._test_connection)
        server_menu.add_command(label="Verificar Recursos", command=self._check_resources)
        menubar.add_cascade(label="Servidor", menu=server_menu)
        
        # Menu SPAdes
        spades_menu = tk.Menu(menubar, tearoff=0)
        spades_menu.add_command(label="Selecionar Arquivos", command=self._browse_reads)
        spades_menu.add_command(label="Configurar Parâmetros", command=self._show_spades_params)
        menubar.add_cascade(label="SPAdes", menu=spades_menu)
        
        # Menu Ajuda
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Sobre SPAdes", command=self._show_spades_info)
        help_menu.add_command(label="Sobre o Aplicativo", command=self._show_about)
        menubar.add_cascade(label="Ajuda", menu=help_menu)
        
        self.config(menu=menubar)
        
    def _create_widgets(self):
        """Cria os widgets principais da interface"""
        # Criar notebook (abas)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Frame de status (parte inferior)
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=5)
        
        # Barra de progresso
        progress = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        progress.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        # Status
        status_label = ttk.Label(status_frame, textvariable=self.status_var)
        status_label.pack(side=tk.LEFT, padx=5)
        
        # # Frame de log aprimorado
        # self.log_frame = ttk.LabelFrame(self, text="Log de Execução")
        # self.log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # # Log com cores e scrollbar
        # log_frame_internal = ttk.Frame(self.log_frame)
        # log_frame_internal.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Adicionar scrollbar para o log
        # log_scrollbar = ttk.Scrollbar(log_frame_internal)
        # log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # # Texto de log com tags para coloração
        # self.log_text = tk.Text(log_frame_internal, height=10, wrap=tk.WORD, 
        #                        yscrollcommand=log_scrollbar.set)
        # self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # log_scrollbar.config(command=self.log_text.yview)
        
        # # Configurar tags de cores para o log
        # self.log_text.tag_configure("INFO", foreground="black")
        # self.log_text.tag_configure("WARNING", foreground="orange")
        # self.log_text.tag_configure("ERROR", foreground="red")
        # self.log_text.tag_configure("SUCCESS", foreground="green")
        
    def _setup_frames(self):
        """Configura os frames específicos da aplicação"""
        # Frame de configuração
        self.config_frame = ConfigFrame(self.notebook, self.server_profiles, self.status_updater, padding=10)
        self.notebook.add(self.config_frame, text="Configuração")
        
        # Frame unificado de execução e monitoramento
        self.execution_frame = ExecutionFrame(
            self.notebook, 
            self.config_frame, 
            self.job_manager, 
            self.status_updater, 
            padding=10
        )
        self.notebook.add(self.execution_frame, text="Execução e Monitoramento")
        
        # Frame de resultados
        self.results_frame = ResultsFrame(
            self.notebook, 
            self.config_frame, 
            self.job_manager, 
            self.status_updater, 
            padding=10
        )
        self.notebook.add(self.results_frame, text="Resultados")
        
    def _bind_events(self):
        """Vincula eventos dos frames para a classe principal"""
        # Eventos do ConfigFrame
        self.config_frame.bind("<<TestConnection>>", lambda e: self._test_connection())
        
        # Eventos do ExecutionFrame (agora unificado)
        self.execution_frame.bind("<<ConnectToServer>>", lambda e: self._connect_to_server())
        self.execution_frame.bind("<<CheckResources>>", lambda e: self._check_resources())
        self.execution_frame.bind("<<PrepareAndUpload>>", lambda e: self._prepare_and_upload())
        self.execution_frame.bind("<<RunSpades>>", lambda e: self._run_spades())
        self.execution_frame.bind("<<CancelJob>>", lambda e: self._cancel_job())
        self.execution_frame.bind("<<OpenSSHTerminal>>", lambda e: self._open_ssh_terminal())
        
        # Eventos do ResultsFrame - modificado para processar dados do evento
        self.results_frame.bind("<<DownloadResults>>", self._download_results_handler)
        self.results_frame.bind("<<OpenResultsFolder>>", lambda e: self._open_results_folder())
        self.results_frame.bind("<<CleanRemoteFiles>>", lambda e: self._clean_remote_files())  # Adicionar esse evento
        
    def _test_connection(self):
        """Testa a conexão com o servidor atual"""
        # Obter parâmetros de conexão
        params = self.config_frame.get_connection_params()
        
        # Validar campos obrigatórios
        if not params["host"]:
            self.status_updater.update_log("Informe o endereço do servidor", "ERROR")
            messagebox.showerror("Erro", "Informe o endereço do servidor")
            return
            
        if not params["username"]:
            self.status_updater.update_log("Informe o nome de usuário", "ERROR")
            messagebox.showerror("Erro", "Informe o nome de usuário")
            return
            
        # Validar método de autenticação
        if params["use_key"]:
            if not params["key_path"] or not os.path.isfile(params["key_path"]):
                self.status_updater.update_log("Arquivo de chave inválido ou não encontrado", "ERROR")
                messagebox.showerror("Erro", "Arquivo de chave inválido ou não encontrado")
                return
        else:
            if not params["password"]:
                self.status_updater.update_log("Senha não informada", "ERROR")
                messagebox.showerror("Erro", "Informe a senha do usuário")
                return
                
        # Testar conexão em thread separada
        threading.Thread(
            target=self._do_test_connection,
            args=(params["host"], params["port"], params["username"], 
                  params["password"], params["key_path"], params["use_key"]),
            daemon=True
        ).start()
        
    def _do_test_connection(self, host, port, username, password, key_path, use_key):
        """Executa o teste de conexão em thread separada"""
        # Desconectar se já estiver conectado
        if self.job_manager.connected:
            self.job_manager.disconnect()
            
        # Testar conexão
        success = self.job_manager.connect(host, port, username, password, key_path, use_key)
        
        if success:
            # Se conectou mas SPAdes não foi encontrado, exibir diálogo para configurar manualmente
            if not self.job_manager.spades_path:
                path_dialog = SpadesPathDialog(self, self.job_manager, self.status_updater)
                if not path_dialog.result:
                    # Usuário cancelou ou não conseguiu configurar
                    self.job_manager.disconnect()
                    messagebox.showerror("Erro", "Não foi possível configurar o SPAdes. A conexão será encerrada.")
                    return
            # Verificar versão do SPAdes
            try:
                # Usar o caminho do SPAdes encontrado durante a conexão
                spades_command = self.job_manager.spades_path if self.job_manager.spades_path else "spades.py"
                stdin, stdout, stderr = self.job_manager.ssh.exec_command(f"{spades_command} --version")
                version = stdout.read().decode().strip()
                self.status_updater.update_log(f"Versão do SPAdes: {version}", "SUCCESS")
            except Exception as e:
                self.status_updater.update_log(f"Não foi possível determinar a versão do SPAdes: {str(e)}", "WARNING")
                
            # Verificar recursos básicos
            resources = self.job_manager.check_server_resources()
            if resources:
                self.execution_frame.update_server_info(resources)
                
            # Desconectar após o teste
            self.job_manager.disconnect()
            
            # Mostrar mensagem de sucesso
            messagebox.showinfo("Sucesso", "Conexão com o servidor estabelecida com sucesso!")
        else:
            messagebox.showerror("Erro", "Falha ao conectar com o servidor. Verifique o log para mais detalhes.")
        
    def _connect_to_server(self):
        """Conecta ao servidor configurado"""
        # Obter parâmetros de conexão
        params = self.config_frame.get_connection_params()
        
        # Validar campos obrigatórios
        if not params["host"] or not params["username"]:
            self.status_updater.update_log("Informe o servidor e o usuário", "WARNING")
            messagebox.showwarning("Atenção", "Informe o endereço do servidor e o nome de usuário.")
            return False
            
        # Validar método de autenticação
        if params["use_key"]:
            if not params["key_path"] or not os.path.isfile(params["key_path"]):
                self.status_updater.update_log("Arquivo de chave inválido ou não encontrado", "ERROR")
                messagebox.showerror("Erro", "Arquivo de chave inválido ou não encontrado.")
                return False
        else:
            if not params["password"]:
                self.status_updater.update_log("Senha não informada", "WARNING")
                messagebox.showerror("Erro", "Informe a senha do usuário.")
                return False
            
        # Desconectar se já estiver conectado
        if self.job_manager.connected:
            self.job_manager.disconnect()
            
         # Conectar em thread separada
        connect_thread = threading.Thread(
            target=self._do_connect,
            args=(params["host"], params["port"], params["username"], 
                  params["password"], params["key_path"], params["use_key"]),
            daemon=True
        )
        connect_thread.start()
        
        # Aguardar um pouco para ver se a conexão é bem sucedida
        connect_thread.join(2.0)
        
        # Se conectado mas SPAdes não encontrado, exibir diálogo para configurar manualmente
        if self.job_manager.connected and not self.job_manager.spades_path:
            path_dialog = SpadesPathDialog(self, self.job_manager, self.status_updater)
            if not path_dialog.result:
                # Usuário cancelou ou não conseguiu configurar
                self.job_manager.disconnect()
                return False
                
        return self.job_manager.connected
            
    def _do_connect(self, host, port, username, password, key_path, use_key):
        """Executa a conexão em thread separada"""
        # Conectar ao servidor
        success = self.job_manager.connect(host, port, username, password, key_path, use_key)
        
        if success:
            # Verificar recursos após conectar
            resources = self.job_manager.check_server_resources()
            if resources:
                self.execution_frame.update_server_info(resources)
                
            # Mostrar mensagem de sucesso
            self.status_updater.update_log(f"Conectado com sucesso a {username}@{host}", "SUCCESS")
            messagebox.showinfo("Sucesso", "Conexão com o servidor estabelecida com sucesso!")
        else:
            messagebox.showerror("Erro", "Falha ao conectar com o servidor. Verifique o log para mais detalhes.")
            
    def _check_resources(self):
        """Verifica os recursos disponíveis no servidor"""
        if not self.job_manager.connected:
            if not self._connect_to_server():
                return
                
        # Verificar recursos em thread separada
        threading.Thread(target=self._do_check_resources, daemon=True).start()
        
    def _do_check_resources(self):
        """Executa a verificação de recursos em thread separada"""
        resources = self.job_manager.check_server_resources()
        
        if resources:
            # Atualizar informações do servidor
            self.execution_frame.update_server_info(resources)
            self.status_updater.update_log("Recursos do servidor verificados", "SUCCESS")
        else:
            self.status_updater.update_log("Não foi possível obter informações de recursos", "ERROR")
            
    def _prepare_and_upload(self):
        """Prepara o diretório remoto e envia os arquivos"""
        if not self.job_manager.connected:
            if not self._connect_to_server():
                return
                
        # Obter parâmetros
        params = self.config_frame.get_spades_params()
            
        # Verificar arquivos
        if not params["read1_path"] or not params["read2_path"]:
            self.status_updater.update_log("Selecione os arquivos de leitura (R1 e R2)", "WARNING")
            messagebox.showwarning("Atenção", "Selecione os arquivos de leitura (R1 e R2).")
            return
            
        if not os.path.exists(params["read1_path"]) or not os.path.exists(params["read2_path"]):
            self.status_updater.update_log("Arquivo de leitura não encontrado", "ERROR")
            messagebox.showerror("Erro", "Um ou mais arquivos de leitura não foram encontrados.")
            return
            
        # Verificar diretório remoto
        if not params["remote_dir"]:
            self.status_updater.update_log("Informe o diretório remoto", "WARNING")
            messagebox.showwarning("Atenção", "Informe o diretório remoto.")
            return
            
        # Preparar e enviar em thread separada
        threading.Thread(
            target=self._do_prepare_and_upload,
            args=(params["remote_dir"], params["read1_path"], params["read2_path"]),
            daemon=True
        ).start()
        
    def _do_prepare_and_upload(self, remote_dir, read1_path, read2_path):
        """Executa a preparação e envio de arquivos em thread separada"""
        # Preparar diretório remoto
        if not self.job_manager.prepare_remote_dir(remote_dir):
            return
            
        # Enviar arquivos
        files_to_upload = [read1_path, read2_path]
        success = self.job_manager.upload_files(files_to_upload, remote_dir)
        
        if success:
            self.status_updater.update_status("Arquivos enviados com sucesso")
            self.execution_frame.update_job_status("Arquivos enviados ao servidor. Pronto para iniciar o SPAdes.")
            messagebox.showinfo("Sucesso", "Arquivos enviados com sucesso ao servidor.")
            
    def _run_spades(self):
        """Inicia a execução do SPAdes no servidor"""
        if not self.job_manager.connected:
            if not self._connect_to_server():
                return
                
        # Verificar se os arquivos foram enviados
        if not self.job_manager.ssh:
            self.status_updater.update_log("Servidor não conectado", "ERROR")
            messagebox.showerror("Erro", "Servidor não conectado. Conecte-se primeiro.")
            return
            
        # Obter parâmetros
        params = self.config_frame.get_spades_params()
            
        # Verificar campos obrigatórios
        if not params["threads"]:
            self.status_updater.update_log("Informe o número de threads", "WARNING")
            messagebox.showwarning("Atenção", "Informe o número de threads a serem utilizados.")
            return
            
        # Verificar se job já está rodando
        if self.job_manager.job_running:
            if not messagebox.askyesno("Job em Execução", "Já existe um job em execução. Deseja iniciar um novo?"):
                return
                
        # Iniciar SPAdes em thread separada
        threading.Thread(
            target=self._do_run_spades,
            args=(
                params["remote_dir"],
                params["read1_path"],
                params["read2_path"],
                params["output_dir"],
                params["threads"],
                params["memory"],
                params["mode"],
                params["kmer"]
            ),
            daemon=True
        ).start()
        
    def _do_run_spades(self, remote_dir, read1_path, read2_path, output_dir, threads, memory, mode, kmer):
        """Executa o SPAdes em thread separada"""
         # Verificar se job já está rodando
        if self.job_manager.job_running:
            if not messagebox.askyesno("Job em Execução", "Já existe um job em execução. Deseja iniciar um novo?"):
                return
                
        # Verificar se o SPAdes funciona antes de tentar executar
        spades_command = self.job_manager.spades_path if self.job_manager.spades_path else "spades.py"
        stdin, stdout, stderr = self.job_manager.ssh.exec_command(f"{spades_command} --help | head -n 5")
        help_output = stdout.read().decode().strip()
        
        if "SPAdes" not in help_output:
            self.status_updater.update_log("O comando SPAdes não está funcionando corretamente.", "ERROR")
            messagebox.showerror("Erro", "O comando SPAdes não está funcionando corretamente. Verifique se está instalado no servidor.")
            path_dialog = SpadesPathDialog(self, self.job_manager, self.status_updater)
            if not path_dialog.result:
                return
                
        # Mostrar uma confirmação com o comando que será executado
        params = self.config_frame.get_spades_params()
        # Usar o caminho do SPAdes que foi detectado durante a conexão
        spades_command = self.job_manager.spades_path if self.job_manager.spades_path else "spades.py"
        cmd_preview = f"{spades_command} -1 {os.path.basename(params['read1_path'])} -2 {os.path.basename(params['read2_path'])} -t {params['threads']} --{params['mode']} -o {params['output_dir']}"
        
        if not messagebox.askyesno("Confirmar Execução", 
            f"O seguinte comando será executado no servidor:\n\n{cmd_preview}\n\nDeseja continuar?"):
            return
            
        # Parâmetros
        memory_param = memory if memory else None
        
        # Iniciar o monitoramento
        self.status_updater.update_status("Executando SPAdes...")
        self.execution_frame.start_monitoring()
        self.notebook.select(self.notebook.index(self.execution_frame))  # Mudar para a aba unificada
        
        # Executar SPAdes
        success = self.job_manager.run_spades(
            remote_dir,
            read1_path,
            read2_path,
            output_dir,
            threads,
            memory_param,
            mode,
            kmer
        )
        
        if success:
            # Certifique-se de que o caminho completo do job_output_file seja definido corretamente
            self.execution_frame.update_job_status(f"SPAdes iniciado. Monitorando progresso em {remote_dir}/{output_dir}...")
            
            # Certificar-se de que o frame de execução está visível
            self.notebook.select(self.notebook.index(self.execution_frame))
            
    def _cancel_job(self):
        """Cancela o job em execução"""
        if not self.job_manager.connected or not self.job_manager.job_running:
            self.status_updater.update_log("Nenhum job em execução para cancelar", "WARNING")
            messagebox.showwarning("Atenção", "Nenhum job em execução para cancelar.")
            return
            
        # Confirmar cancelamento
        if messagebox.askyesno("Confirmar Cancelamento", "Deseja realmente cancelar o job em execução?"):
            # Cancelar em thread separada
            threading.Thread(target=self._do_cancel_job, daemon=True).start()
            
    def _do_cancel_job(self):
        """Executa o cancelamento do job em thread separada"""
        success = self.job_manager.cancel_job()
        
        if success:
            self.execution_frame.update_job_status("Job cancelado pelo usuário.")
            self.execution_frame.stop_monitoring()
            
            # Perguntar ao usuário se deseja limpar os arquivos do job cancelado
            # Neste momento a conexão SSH ainda está ativa
            if messagebox.askyesno("Limpar Arquivos", 
                                  "Job cancelado com sucesso. Deseja limpar os arquivos remotos do job cancelado?"):
                # Obter parâmetros do job
                params = self.config_frame.get_spades_params()
                
                # Verificar se a conexão está ativa antes de prosseguir
                if not self.job_manager.connected or not self.job_manager.ssh or (
                    hasattr(self.job_manager.ssh, 'get_transport') and (
                        not self.job_manager.ssh.get_transport() or 
                        not self.job_manager.ssh.get_transport().is_active()
                    )):
                    # Tentar reconectar se a sessão já foi encerrada
                    if not self._connect_to_server():
                        messagebox.showwarning("Aviso", 
                            "A conexão SSH foi perdida. Reconecte ao servidor e tente limpar os arquivos manualmente.")
                        return
                
                # Chamar a função de limpeza específica para o diretório do job
                self._do_clean_remote_files(params["remote_dir"], params["output_dir"])
            else:
                messagebox.showinfo("Sucesso", "Job cancelado com sucesso.")
        else:
            messagebox.showerror("Erro", "Não foi possível cancelar o job. Verifique o log para mais detalhes.")
    
    def _open_ssh_terminal(self):
        """Abre um terminal com comando SSH pronto para conectar ao servidor"""
        # Obter parâmetros de conexão
        params = self.config_frame.get_connection_params()
        
        # Validar campos obrigatórios
        if not params["host"] or not params["username"]:
            self.status_updater.update_log("Informe o servidor e o usuário para abrir terminal SSH", "WARNING")
            messagebox.showwarning("Atenção", "Informe o endereço do servidor e o nome de usuário.")
            return
            
        # Determinar se deve usar arquivo de chave
        key_path = None
        if params["use_key"] and params["key_path"] and os.path.isfile(params["key_path"]):
            key_path = params["key_path"]
            
        # Abrir o terminal
        success = open_ssh_terminal(
            params["host"], 
            params["port"],
            params["username"],
            key_path
        )
        
        if success:
            # Verificar se a porta é padrão (22) ou não
            port_info = f" (porta {params['port']})" if params['port'] != "22" else ""
            self.status_updater.update_log(f"Terminal SSH aberto para {params['username']}@{params['host']}{port_info}", "SUCCESS")
        else:
            self.status_updater.update_log("Não foi possível abrir o terminal SSH", "ERROR")
            messagebox.showerror("Erro", "Não foi possível abrir o terminal SSH. Verifique se o terminal está disponível no seu sistema.")
            
    def _download_results_handler(self, event):
        """Manipulador para evento de download de resultados"""
        # Tentar obter dados do evento, padrão para True se não for especificado
        try:
            event_data = event.data if hasattr(event, 'data') else {}
            important_only = event_data.get("important_only", True)
        except:
            important_only = True
        
        self._download_results(important_only)

    def _download_results(self, important_only=True):
        """
        Baixa os resultados do servidor
        
        Args:
            important_only: Se True, baixa apenas os arquivos importantes
        """
        if not self.job_manager.connected:
            if not self._connect_to_server():
                return
                
        # Obter parâmetros
        params = self.config_frame.get_spades_params()
                
        # Verificar se o job ainda está rodando
        if self.job_manager.job_running:
            if not messagebox.askyesno("Job em Execução", "O job ainda está em execução. Deseja baixar resultados parciais?"):
                return
                
        # Verificar diretório local
        local_dir = params["local_output_dir"]
        if not local_dir:
            local_dir = os.path.join(os.getcwd(), "spades_results")
            self.config_frame.local_output_dir.set(local_dir)
            
        # Informação sobre o tipo de download
        download_type = "arquivos importantes" if important_only else "todos os arquivos"
        self.status_updater.update_log(f"Iniciando download de {download_type}...", "INFO")
            
        # Baixar em thread separada
        threading.Thread(
            target=self._do_download_results,
            args=(params["remote_dir"], params["output_dir"], local_dir, important_only),
            daemon=True
        ).start()
        
    def _do_download_results(self, remote_dir, output_dir, local_dir, important_only):
        """
        Executa o download dos resultados em thread separada
        
        Args:
            remote_dir: Diretório remoto
            output_dir: Diretório de saída
            local_dir: Diretório local
            important_only: Se True, baixa apenas arquivos importantes
        """
        success = self.job_manager.download_results(remote_dir, output_dir, local_dir, important_only)
        
        if success:
            # Atualizar lista de arquivos baixados
            self.results_frame.update_results_list(local_dir, output_dir)
            
            # Mostrar mensagem de sucesso
            download_type = "arquivos importantes" if important_only else "todos os arquivos"
            messagebox.showinfo("Sucesso", f"{download_type.capitalize()} baixados com sucesso.")
            
            # Mudar para a aba de resultados
            self.notebook.select(self.notebook.index(self.results_frame))

    def _open_results_folder(self):
        """Abre o diretório de resultados no explorador de arquivos"""
        params = self.config_frame.get_spades_params()
        local_output_path = os.path.join(params["local_output_dir"], params["output_dir"])
        
        if not os.path.exists(local_output_path):
            self.status_updater.update_log(f"Diretório de resultados não encontrado: {local_output_path}", "WARNING")
            messagebox.showwarning("Atenção", f"Diretório de resultados não encontrado: {local_output_path}")
            return
            
        # Abrir diretório no explorador de arquivos
        try:
            if platform.system() == "Windows":
                os.startfile(local_output_path)
            elif platform.system() == "Darwin":  # macOS
                import subprocess
                subprocess.run(["open", local_output_path], check=True)
            else:  # Linux
                import subprocess
                subprocess.run(["xdg-open", local_output_path], check=True)
                
            self.status_updater.update_log(f"Diretório aberto: {local_output_path}")
        except Exception as e:
            self.status_updater.update_log(f"Erro ao abrir diretório: {str(e)}", "ERROR")
            messagebox.showerror("Erro", f"Erro ao abrir diretório: {str(e)}")
            
    def _save_log(self):
        """Salva o log em arquivo"""
        filename = filedialog.asksaveasfilename(
            title="Salvar Log",
            defaultextension=".txt",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        
        if filename:
            try:
                # Pegar o conteúdo do log no ExecutionFrame
                log_content = self.execution_frame.log_text.get(1.0, tk.END)
                with open(filename, 'w') as f:
                    f.write(log_content)
                self.status_updater.update_log(f"Log salvo em: {filename}", "SUCCESS")
            except Exception as e:
                self.status_updater.update_log(f"Erro ao salvar log: {str(e)}", "ERROR")
                
    def _browse_reads(self):
        """Abre diálogo para selecionar arquivos de leitura"""
        # Método que chama a função correspondente no ConfigFrame
        self.config_frame._browse_reads()
                
    def _show_profile_manager(self):
        """Mostra o diálogo de gerenciamento de perfis"""
        ProfileManagerDialog(self, self.server_profiles, self.config_frame._load_server_profiles)
                
    def _show_spades_params(self):
        """Mostra diálogo com parâmetros avançados do SPAdes"""
        SPAdesParamsDialog(self, self.config_frame)
        
    def _show_spades_info(self):
        """Mostra informações sobre o SPAdes"""
        info = """
SPAdes (St. Petersburg genome assembler) é um montador de genoma desenvolvido pelo Centro de Algoritmos Bioinformáticos da Universidade de São Petersburgo.

Características:
- Montagem de genomas de novo a partir de sequências curtas (Illumina) e longas (PacBio, ONT)
- Correção de erros integrada
- Modos especializados: isolado, meta, plasmídeo, RNA, célula única
- Utiliza grafos de De Bruijn com múltiplos k-mers

Opções comuns:
- -1, -2: Arquivos de leituras paired-end
- -t: Número de threads
- -m: Memória máxima (GB)
- -k: Valores de k-mer
- --careful: Reduz número de misassemblies
- --isolate, --meta, etc.: Modos de execução

Mais informações: http://cab.spbu.ru/software/spades/
"""
        messagebox.showinfo("Sobre o SPAdes", info)
        
    def _show_about(self):
        """Mostra informações sobre o aplicativo"""
        about = f"""
{APP_NAME} - Gerenciador de Montagens

Versão: {APP_VERSION}

Um aplicativo para gerenciar execuções remotas do SPAdes, permitindo:
- Configuração e gerenciamento de servidores
- Envio de arquivos para processamento remoto
- Monitoramento de execução
- Download de resultados

Desenvolvido para facilitar o uso do SPAdes em ambientes computacionais distribuídos.
"""
        messagebox.showinfo("Sobre o Aplicativo", about)
        
    # Adicionar método para tratar o fim da execução
    def _job_finished(self, success, message):
        """Tratamento após o término do job"""
        self.execution_frame.stop_monitoring()
        if success:
            self.status_updater.update_log(message, "SUCCESS")
            messagebox.showinfo("Concluído", message)
            self.notebook.select(self.notebook.index(self.results_frame))  # Mudar para a aba de resultados
        else:
            self.status_updater.update_log(message, "ERROR")
            messagebox.showerror("Erro", message)
            
    def _clean_remote_files(self):
        """Limpa os arquivos remotos no servidor"""
        if not self.job_manager.connected:
            if not self._connect_to_server():
                return
        
        # Verificar se job está em execução
        if self.job_manager.job_running:
            self.status_updater.update_log("Não é possível limpar arquivos enquanto um job está em execução", "WARNING")
            messagebox.showwarning("Atenção", "Não é possível limpar arquivos enquanto um job está em execução.")
            return
        
        # Obter parâmetros
        params = self.config_frame.get_spades_params()
        
        # Confirmar com o usuário antes de prosseguir
        if params["output_dir"]:
            msg = f"Esta operação removerá o diretório '{params['output_dir']}' de '{params['remote_dir']}' no servidor.\nEsta ação não pode ser desfeita. Continuar?"
        else:
            msg = f"Esta operação removerá TODOS OS ARQUIVOS de '{params['remote_dir']}' no servidor.\nEsta ação não pode ser desfeita. Continuar?"
        
        if not messagebox.askyesno("Confirmar Limpeza", msg, icon="warning"):
            self.status_updater.update_log("Operação de limpeza cancelada pelo usuário")
            return
        
        # Iniciar thread para limpeza
        threading.Thread(
            target=self._do_clean_remote_files,
            args=(params["remote_dir"], params["output_dir"]),
            daemon=True
        ).start()

    def _do_clean_remote_files(self, remote_dir, output_dir=None):
        """
        Executa a limpeza de arquivos remotos em thread separada
        
        Args:
            remote_dir: Diretório remoto
            output_dir: Diretório específico de saída (opcional)
        """
        # Verificar se ainda estamos conectados, reconectar se necessário
        if not self.job_manager.connected or not self.job_manager.ssh or (
            hasattr(self.job_manager.ssh, 'get_transport') and (
                not self.job_manager.ssh.get_transport() or 
                not self.job_manager.ssh.get_transport().is_active()
            )):
            self.status_updater.update_log("Sessão SSH não está ativa. Tentando reconectar...", "WARNING")
            if not self._connect_to_server():
                self.status_updater.update_log("Não foi possível reconectar ao servidor. Impossível limpar arquivos.", "ERROR")
                messagebox.showerror("Erro", "A conexão SSH foi perdida e não foi possível reconectar. Tente novamente mais tarde.")
                return
                
        # Mostrar mensagem de processamento
        self.status_updater.update_status("Limpando arquivos remotos...")
        self.status_updater.update_log("Iniciando limpeza de arquivos remotos...", "INFO")
        
        # Chamar método do job_manager para limpar
        success, message = self.job_manager.clean_remote_files(remote_dir, output_dir)
        
        if success:
            # Mostrar mensagem de sucesso
            self.status_updater.update_status("Arquivos remotos limpos com sucesso")
            self.status_updater.update_log(message, "SUCCESS")
            messagebox.showinfo("Sucesso", f"Arquivos remotos limpos com sucesso.\n\n{message}")
        else:
            # Mostrar mensagem de erro
            self.status_updater.update_status("Erro ao limpar arquivos remotos")
            self.status_updater.update_log(message, "ERROR")
            messagebox.showerror("Erro", f"Erro ao limpar arquivos remotos.\n\n{message}")
