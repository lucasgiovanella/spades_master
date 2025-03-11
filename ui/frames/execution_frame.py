#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime
import os
from ui.styles import ResponsiveUI

class ExecutionFrame(ttk.Frame):
    """Frame unificado para execução e monitoramento de jobs SPAdes com log integrado"""
    def __init__(self, parent, config_frame, job_manager, status_updater, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.parent = parent
        self.config_frame = config_frame
        self.job_manager = job_manager
        self.status_updater = status_updater
        
        # Variáveis de monitoramento
        self.start_time = None
        self.elapsed_time_var = tk.StringVar(value="00:00:00")
        self.cpu_usage_var = tk.StringVar(value="0%")
        self.memory_usage_var = tk.StringVar(value="0 MB")
        self.current_phase_var = tk.StringVar(value="Aguardando")
        self.monitoring = False
        self.update_timer = None
        
        # Criar interface
        self._create_widgets()
        
        # Registrar handler personalizado para o status_updater
        self.original_log_handler = status_updater.update_log
        status_updater.update_log = self._custom_log_handler
        
    def _create_widgets(self):
        """Cria os widgets do frame unificado"""
        # Obter a instância de ResponsiveUI do aplicativo principal
        self.responsive_ui = self.parent.master.responsive_ui if hasattr(self.parent, 'master') and hasattr(self.parent.master, 'responsive_ui') else None
        
        # Definir padding responsivo
        padding = self.responsive_ui.get_padding() if self.responsive_ui else 10
        
        # Frame principal dividido verticalmente
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=padding, pady=padding//2)
        
        # Frame superior para controles e métricas
        top_frame = ttk.Frame(main_frame, style='Card.TFrame')
        top_frame.pack(fill=tk.X, pady=padding//2)
        
        # Frame para log centralizado (ocupará a maior parte da tela)
        log_frame = ttk.LabelFrame(main_frame, text="Log de Execução Unificado", style='Card.TFrame')
        log_frame.pack(fill=tk.BOTH, expand=True, pady=padding//2)
        
        # Dividir top_frame em dois painéis horizontais
        controls_pane = ttk.PanedWindow(top_frame, orient=tk.HORIZONTAL)
        controls_pane.pack(fill=tk.X, expand=True)
        
        # Painel esquerdo - Informações e controles
        left_control_frame = ttk.Frame(controls_pane, style='Card.TFrame')
        controls_pane.add(left_control_frame, weight=3)
        
        # Painel direito - Métricas
        right_metrics_frame = ttk.Frame(controls_pane, style='Card.TFrame')
        controls_pane.add(right_metrics_frame, weight=2)
        
        # === PAINEL ESQUERDO ===
        # Informações do servidor
        server_info_frame = ttk.LabelFrame(left_control_frame, text="Informações do Servidor", style='Card.TFrame')
        server_info_frame.pack(fill=tk.X, padx=padding//2, pady=padding//2)
        
        self.server_info_text = tk.Text(server_info_frame, height=4, width=40, state='disabled')
        self.server_info_text.pack(fill=tk.X, padx=5, pady=5)
        
        # Botões de ação
        button_frame = ttk.Frame(left_control_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Grid para organizar botões melhor
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        
        # Primeira linha de botões
        ttk.Button(
            button_frame, 
            text="Conectar ao Servidor", 
            command=self._connect_to_server
        ).grid(row=0, column=0, padx=2, pady=2, sticky="ew")
        
        ttk.Button(
            button_frame, 
            text="Verificar Recursos", 
            command=self._check_resources
        ).grid(row=0, column=1, padx=2, pady=2, sticky="ew")
        
        ttk.Button(
            button_frame, 
            text="Abrir Terminal SSH", 
            command=self._open_ssh_terminal
        ).grid(row=0, column=2, padx=2, pady=2, sticky="ew")
        
        # Segunda linha de botões
        ttk.Button(
            button_frame, 
            text="Preparar e Enviar Arquivos", 
            command=self._prepare_and_upload
        ).grid(row=1, column=0, padx=2, pady=2, sticky="ew")
        
        ttk.Button(
            button_frame, 
            text="Iniciar SPAdes", 
            command=self._run_spades,
            style="Accent.TButton"
        ).grid(row=1, column=1, padx=2, pady=2, sticky="ew")
        
        ttk.Button(
            button_frame, 
            text="Cancelar Job", 
            command=self._cancel_job
        ).grid(row=1, column=2, padx=2, pady=2, sticky="ew")
        
        # === PAINEL DIREITO ===
        # Monitor de recursos
        resources_frame = ttk.LabelFrame(right_metrics_frame, text="Monitor de Recursos")
        resources_frame.pack(fill=tk.BOTH, padx=5, pady=5)
        
        # Grade de métricas
        metrics_grid = ttk.Frame(resources_frame)
        metrics_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # Configuração do grid
        metrics_grid.columnconfigure(1, weight=1)
        
        # Tempo decorrido
        ttk.Label(metrics_grid, text="Tempo de execução:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=3)
        ttk.Label(metrics_grid, textvariable=self.elapsed_time_var).grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)
        
        # Uso de CPU
        ttk.Label(metrics_grid, text="Uso de CPU:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=3)
        self.cpu_progress = ttk.Progressbar(metrics_grid, mode='determinate', length=150)
        self.cpu_progress.grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)
        ttk.Label(metrics_grid, textvariable=self.cpu_usage_var).grid(row=1, column=2, sticky=tk.W, padx=5, pady=3)
        
        # Uso de memória
        ttk.Label(metrics_grid, text="Uso de memória:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=3)
        self.memory_progress = ttk.Progressbar(metrics_grid, mode='determinate', length=150)
        self.memory_progress.grid(row=2, column=1, sticky=tk.W, padx=5, pady=3)
        ttk.Label(metrics_grid, textvariable=self.memory_usage_var).grid(row=2, column=2, sticky=tk.W, padx=5, pady=3)
        
        # Fase atual
        ttk.Label(metrics_grid, text="Fase atual:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=3)
        self.phase_label = ttk.Label(metrics_grid, textvariable=self.current_phase_var, wraplength=200)
        self.phase_label.grid(row=3, column=1, sticky=tk.W, padx=5, pady=3, columnspan=2)
        
        # Tabela de processos
        processes_frame = ttk.LabelFrame(resources_frame, text="Processos Ativos")
        processes_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Criar treeview para processos
        processes_columns = ("pid", "name", "cpu", "memory")
        self.processes_tree = ttk.Treeview(processes_frame, columns=processes_columns, show="headings", height=4)
        
        # Configurar cabeçalhos
        self.processes_tree.heading("pid", text="PID")
        self.processes_tree.heading("name", text="Processo")
        self.processes_tree.heading("cpu", text="CPU %")
        self.processes_tree.heading("memory", text="MEM %")
        
        # Configurar colunas
        self.processes_tree.column("pid", width=50)
        self.processes_tree.column("name", width=120)
        self.processes_tree.column("cpu", width=60)
        self.processes_tree.column("memory", width=60)
        
        # Adicionar scrollbar
        processes_scrollbar = ttk.Scrollbar(processes_frame, orient=tk.VERTICAL, command=self.processes_tree.yview)
        self.processes_tree.configure(yscrollcommand=processes_scrollbar.set)
        
        # Empacotar treeview e scrollbar
        self.processes_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        processes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Barra de progresso
        self.progress_bar = ttk.Progressbar(resources_frame, mode='indeterminate')
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # === LOG CENTRALIZADO ===
        # Container para log com scrollbar
        log_container = ttk.Frame(log_frame)
        log_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbar vertical
        log_scrollbar = ttk.Scrollbar(log_container)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Texto de log unificado
        self.log_text = tk.Text(log_container, wrap=tk.WORD, yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.config(command=self.log_text.yview)
        
        # Configurar tags para coloração
        self.log_text.tag_configure("INFO", foreground="black")
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("SUCCESS", foreground="green")
        self.log_text.tag_configure("PHASE", foreground="blue", font=("TkDefaultFont", 9, "bold"))
        self.log_text.tag_configure("COMMAND", foreground="purple")
        self.log_text.tag_configure("METRICS", foreground="teal")
        
        # Botões de controle do log
        log_buttons = ttk.Frame(log_frame)
        log_buttons.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Button(log_buttons, text="Limpar Log", command=self._clear_log).pack(side=tk.RIGHT, padx=2)
        
    def _custom_log_handler(self, message, level="INFO"):
        """Intercepta chamadas de log e as redireciona para o log unificado"""
        self._add_to_log(message, level)
        # Também chamar o handler original para manter a funcionalidade esperada
        self.original_log_handler(message, level)
        
    def _add_to_log(self, message, level="INFO"):
        """Adiciona uma entrada ao log unificado"""
        try:
            self.log_text.config(state=tk.NORMAL)
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_text = f"[{timestamp}] [{level}] {message}\n"
            
            self.log_text.insert(tk.END, formatted_text, level)
            self.log_text.see(tk.END)
            
            self.log_text.config(state=tk.DISABLED)
        except Exception:
            # Evitar erros se chamado antes da inicialização da interface
            pass
            
    def _clear_log(self):
        """Limpa o conteúdo do log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)
        
        # Registrar a limpeza
        self._add_to_log("Log limpo pelo usuário", "INFO")

    def update_server_info(self, resources):
        """Atualiza a exibição de informações do servidor"""
        info_text = self.server_info_text
        info_text.config(state='normal')
        info_text.delete(1.0, tk.END)
        
        params = self.config_frame.get_connection_params()
        
        # Verificar se a porta é padrão (22) ou não
        port_info = f" (porta {params['port']})" if params['port'] != "22" else ""
        info_text.insert(tk.END, f"Servidor: {params['host']}{port_info}\n")
        info_text.insert(tk.END, f"Usuário: {params['username']}\n")
        
        # Adicionar informações de recursos
        if resources:
            if isinstance(resources["cpu_count"], int):
                info_text.insert(tk.END, f"CPUs disponíveis: {resources['cpu_count']}\n")
            else:
                info_text.insert(tk.END, f"CPUs: {resources['cpu_count']}\n")
                
            if isinstance(resources["total_mem"], int) and isinstance(resources["free_mem"], int):
                info_text.insert(tk.END, f"Memória total: {resources['total_mem']} MB ({resources['total_mem']/1024:.1f} GB)\n")
                info_text.insert(tk.END, f"Memória livre: {resources['free_mem']} MB ({resources['free_mem']/1024:.1f} GB)\n")
            else:
                info_text.insert(tk.END, f"Memória total: {resources['total_mem']}\n")
                info_text.insert(tk.END, f"Memória livre: {resources['free_mem']}\n")
                
            info_text.insert(tk.END, f"Espaço em disco disponível: {resources['disk_avail']}\n")
        
        info_text.config(state='disabled')
        
        # Adicionar ao log também
        self._add_to_log(f"Servidor conectado: {params['username']}@{params['host']}{port_info}", "SUCCESS")
        if resources:
            self._add_to_log(f"Recursos do servidor: CPUs={resources['cpu_count']}, Memória={resources['total_mem']} MB, Livre={resources['free_mem']} MB", "INFO")
        
    def update_job_status(self, initial_message=None):
        """Atualiza o status do job e adiciona ao log"""
        if initial_message:
            self._add_to_log(initial_message, "PHASE")
        
        if self.job_manager.job_running and self.job_manager.job_pid:
             # Obter status do processo
            try:
                stdin, stdout, stderr = self.job_manager.ssh.exec_command(
                    f"ps -p {self.job_manager.job_pid} -o pid,pcpu,pmem,time,comm | grep -v PID || echo 'NOT_RUNNING'"
                )
                process_info = stdout.read().decode().strip()
                
                if process_info == 'NOT_RUNNING':
                    self._add_to_log("O processo não está em execução", "WARNING")
                else:
                    self._add_to_log(f"Status do processo: {process_info}", "INFO")
                    
                # Obter últimas linhas do log
                if self.job_manager.job_output_file:
                    stdin, stdout, stderr = self.job_manager.ssh.exec_command(
                        f"tail -n 5 {self.job_manager.job_output_file} 2>/dev/null || echo 'Log não encontrado'"
                    )
                    log_output = stdout.read().decode().strip()
                    
                    if log_output and log_output != 'Log não encontrado':
                        output_lines = log_output.split('\n')
                        if output_lines:
                            for line in output_lines:
                                if line.strip():
                                    self._add_to_log(f"[SPAdes] {line.strip()}", "COMMAND")
            except Exception as e:
                self._add_to_log(f"Erro ao atualizar status: {str(e)}", "ERROR")
                
    def _connect_to_server(self):
        """Conecta ao servidor configurado"""
        # Disparar evento para a classe principal
        self.event_generate("<<ConnectToServer>>")
            
    def _check_resources(self):
        """Verifica os recursos disponíveis no servidor"""
        # Disparar evento para a classe principal
        self.event_generate("<<CheckResources>>")
        
    def _prepare_and_upload(self):
        """Prepara o diretório remoto e envia os arquivos"""
        # Disparar evento para a classe principal
        self.event_generate("<<PrepareAndUpload>>")
        
    def _run_spades(self):
        """Inicia a execução do SPAdes no servidor"""
        # Disparar evento para a classe principal
        self.event_generate("<<RunSpades>>")
        
    def _cancel_job(self):
        """Cancela o job em execução"""
        if not self.job_manager.connected:
            self._add_to_log("Não há conexão com o servidor", "WARNING")
            messagebox.showwarning("Atenção", "Não há conexão com o servidor.")
            return
            
        # Verificar se há processos do SPAdes em execução
        processes_info = self.job_manager.get_user_processes()
        if not processes_info or not processes_info.get('spades_processes'):
            self._add_to_log("Nenhum processo SPAdes detectado em execução", "WARNING")
            
            # Verificar se temos um job_pid ou job_id registrado
            if not self.job_manager.job_pid and not self.job_manager.job_running:
                messagebox.showwarning("Atenção", "Nenhum job SPAdes em execução para cancelar.")
                return
        
        # Confirmar cancelamento
        if messagebox.askyesno("Confirmar Cancelamento", "Deseja realmente cancelar o job em execução?"):
            # Mostrar detalhes dos processos que serão cancelados
            if processes_info and processes_info.get('spades_processes'):
                process_info_text = "\n".join([
                    f"- PID {p['pid']}: {p['cmd'][:50]}..." for p in processes_info['spades_processes'][:5]
                ])
                if len(processes_info['spades_processes']) > 5:
                    process_info_text += f"\n(e mais {len(processes_info['spades_processes']) - 5} processos)"
                    
                self._add_to_log(f"Cancelando os seguintes processos:\n{process_info_text}", "WARNING")
            
            # Disparar evento para a classe principal
            self.event_generate("<<CancelJob>>")
        
    def _open_ssh_terminal(self):
        """Abre um terminal com comando SSH pronto"""
        # Disparar evento para a classe principal
        self.event_generate("<<OpenSSHTerminal>>")
    
    def start_monitoring(self):
        """Iniciar o monitoramento do processo"""
        self.monitoring = True
        self.start_time = datetime.now()
        self.progress_bar.start(10)
        
        self._add_to_log("Iniciando monitoramento do processo", "PHASE")
        self._update_metrics()
    
    def stop_monitoring(self):
        """Parar o monitoramento"""
        self.monitoring = False
        if self.update_timer:
            self.after_cancel(self.update_timer)
            self.update_timer = None
        self.progress_bar.stop()
        self._add_to_log("Monitoramento do processo encerrado", "PHASE")
    
    def _update_metrics(self):
        """Atualizar as métricas do servidor"""
        if not self.monitoring:
            return
            
        # Atualizar tempo decorrido
        if self.start_time:
            elapsed = datetime.now() - self.start_time
            hours, remainder = divmod(int(elapsed.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self.elapsed_time_var.set(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Obter uso de recursos via SSH
        if self.job_manager.ssh and self.job_manager.job_running:
            try:
                # Obter informações de todos os processos do usuário
                process_info = self.job_manager.get_user_processes()
                if process_info:
                    # Atualizar uso de CPU (todos os processos SPAdes)
                    spades_cpu = process_info['spades_cpu']
                    self.cpu_usage_var.set(f"{spades_cpu}%")
                    self.cpu_progress['value'] = min(spades_cpu, 100)  # Limitar a 100%
                    
                    # Atualizar uso de memória (todos os processos SPAdes)
                    spades_mem = process_info['spades_mem']
                    spades_mem_mb = process_info['spades_mem_mb']
                    self.memory_usage_var.set(f"{spades_mem_mb} MB ({spades_mem}%")
                    self.memory_progress['value'] = min(spades_mem, 100)  # Limitar a 100%
                    
                    # Atualizar a tabela de processos
                    self.processes_tree.delete(*self.processes_tree.get_children())
                    
                    # Mostrar os processos principais que estão consumindo mais CPU
                    top_processes = sorted(process_info['spades_processes'], key=lambda x: x['cpu'], reverse=True)[:5]
                    for proc in top_processes:
                        cmd_short = proc['cmd'].split(' ')[0]
                        if '/' in cmd_short:
                            cmd_short = cmd_short.split('/')[-1]
                        
                        # Adicionar à tabela de processos
                        self.processes_tree.insert("", tk.END, values=(
                            proc['pid'],
                            cmd_short,
                            f"{proc['cpu']}%",
                            f"{proc['mem']}%"
                        ))
                
                # Verificar fase atual do SPAdes
                if self.job_manager.job_output_file:
                    stdin, stdout, stderr = self.job_manager.ssh.exec_command(
                        f"grep -E '(===|Stage)' {self.job_manager.job_output_file} | tail -n 1"
                    )
                    phase = stdout.read().decode().strip()
                    if phase:
                        self.current_phase_var.set(phase)
                        self._add_to_log(f"Fase atual: {phase}", "PHASE")
                
                # Atualizar também o status do job
                self.update_job_status()
            
            except Exception as e:
                self._add_to_log(f"Erro ao atualizar métricas: {str(e)}", "ERROR")
        
        # Agendar a próxima atualização
        self.update_timer = self.after(3000, self._update_metrics)