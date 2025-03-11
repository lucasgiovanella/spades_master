#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog
import os
from config.settings import DEFAULT_PORT, DEFAULT_THREADS, DEFAULT_MODE, DEFAULT_REMOTE_DIR, DEFAULT_OUTPUT_DIR
from ui.dialogs.profile_dialog import ProfileDialog, ProfileManagerDialog

class ConfigFrame(ttk.Frame):
    """Frame para configuração do servidor e arquivos"""
    def __init__(self, parent, server_profiles, status_updater, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.parent = parent
        self.server_profiles = server_profiles
        self.status_updater = status_updater
        
        # Initialize responsive UI attribute
        self.responsive_ui = None
        if hasattr(parent.master, 'responsive_ui'):
            self.responsive_ui = parent.master.responsive_ui
        
        # Variáveis para conexão
        self.selected_profile = tk.StringVar()
        self.server_host = tk.StringVar()
        self.server_port = tk.StringVar(value=DEFAULT_PORT)
        self.server_username = tk.StringVar()
        self.server_password = tk.StringVar()
        self.ssh_key_path = tk.StringVar()
        self.use_key_auth = tk.BooleanVar(value=False)
        
        # Variáveis para SPAdes
        self.read1_path = tk.StringVar()
        self.read2_path = tk.StringVar()
        self.remote_dir = tk.StringVar(value=DEFAULT_REMOTE_DIR)
        self.output_dir = tk.StringVar(value=DEFAULT_OUTPUT_DIR)
        self.local_output_dir = tk.StringVar(value=os.path.join(os.getcwd(), "spades_results"))
        self.threads = tk.StringVar(value=DEFAULT_THREADS)
        self.memory = tk.StringVar(value="")
        self.mode = tk.StringVar(value=DEFAULT_MODE)
        self.kmer = tk.StringVar(value="")
        
        # Criar interface
        self._create_widgets()
        
        # Carregar perfis de servidor
        self._load_server_profiles()
    
    def _create_widgets(self):
        """Cria widgets do frame de configuração"""
        # Frame de conexão
        self._create_connection_frame()
        
        # Separador
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10, pady=10)
        
        # Frame de arquivos
        self._create_files_frame()
        
        # Separador
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10, pady=10)
        
        # Frame de parâmetros SPAdes
        self._create_params_frame()
    
    def _create_connection_frame(self):
        """Cria frame de conexão com o servidor"""
        conn_frame = ttk.LabelFrame(self, text="Conexão com o Servidor")
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        # Grid para organizar widgets
        conn_frame.columnconfigure(1, weight=1)
        
        # Perfil
        ttk.Label(conn_frame, text="Perfil:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        profile_frame = ttk.Frame(conn_frame)
        profile_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        self.profile_combo = ttk.Combobox(profile_frame, textvariable=self.selected_profile, state="readonly", width=25)
        self.profile_combo.pack(side="left", fill="x", expand=True)
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_selected)
        
        ttk.Button(profile_frame, text="Novo", command=self._new_profile).pack(side="left", padx=5)
        ttk.Button(profile_frame, text="Gerenciar", command=self._show_profile_manager).pack(side="left")
        
        # Servidor
        ttk.Label(conn_frame, text="Servidor:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        server_frame = ttk.Frame(conn_frame)
        server_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        self.host_entry = ttk.Entry(server_frame, textvariable=self.server_host, width=25)
        self.host_entry.pack(side="left", fill="x", expand=True)
        
        ttk.Label(server_frame, text="Porta:").pack(side="left", padx=5)
        ttk.Entry(server_frame, textvariable=self.server_port, width=7).pack(side="left")
        
        # Usuário
        ttk.Label(conn_frame, text="Usuário:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.username_entry = ttk.Entry(conn_frame, textvariable=self.server_username, width=25)
        self.username_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        # Senha
        ttk.Label(conn_frame, text="Senha:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.password_entry = ttk.Entry(conn_frame, textvariable=self.server_password, show="*", width=25)
        self.password_entry.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        
        # Autenticação por chave
        key_check = ttk.Checkbutton(
            conn_frame, 
            text="Usar chave SSH", 
            variable=self.use_key_auth,
            command=self._toggle_auth_method
        )
        key_check.grid(row=4, column=0, sticky="w", padx=5, pady=5)
        
        # Caminho da chave
        key_frame = ttk.Frame(conn_frame)
        key_frame.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
        
        self.key_entry = ttk.Entry(key_frame, textvariable=self.ssh_key_path, width=25)
        self.key_entry.pack(side="left", fill="x", expand=True)
        
        self.key_button = ttk.Button(key_frame, text="Procurar", command=self._browse_ssh_key)
        self.key_button.pack(side="left", padx=5)
        
        # Botões
        button_frame = ttk.Frame(conn_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Testar Conexão", command=self._test_connection).pack(side="left", padx=10)
        ttk.Button(button_frame, text="Salvar Perfil", command=self._save_current_profile).pack(side="left", padx=10)
        
        # Estado inicial
        self._toggle_auth_method()
    
    def _create_files_frame(self):
        """Cria frame de arquivos"""
        padding = self.responsive_ui.get_padding() if self.responsive_ui else 10
        
        files_frame = ttk.LabelFrame(self, text="Arquivos de Entrada", style='Card.TFrame')
        files_frame.pack(fill="x", padx=padding, pady=padding//2)
        
        # Grid para organizar widgets
        files_frame.columnconfigure(1, weight=1)
        
        # Read 1
        ttk.Label(files_frame, text="Arquivo R1:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        
        read1_frame = ttk.Frame(files_frame)
        read1_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Entry(read1_frame, textvariable=self.read1_path).pack(side="left", fill="x", expand=True)
        ttk.Button(
            read1_frame, 
            text="Procurar", 
            command=lambda: self._browse_file(self.read1_path, "Selecione o arquivo R1")
        ).pack(side="left", padx=5)
        
        # Read 2
        ttk.Label(files_frame, text="Arquivo R2:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        read2_frame = ttk.Frame(files_frame)
        read2_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Entry(read2_frame, textvariable=self.read2_path).pack(side="left", fill="x", expand=True)
        ttk.Button(
            read2_frame, 
            text="Procurar", 
            command=lambda: self._browse_file(self.read2_path, "Selecione o arquivo R2")
        ).pack(side="left", padx=5)
        
        # Diretório remoto
        ttk.Label(files_frame, text="Diretório remoto:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(files_frame, textvariable=self.remote_dir).grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        # Pasta de saída
        ttk.Label(files_frame, text="Pasta de saída:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(files_frame, textvariable=self.output_dir).grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        
        # Diretório local
        ttk.Label(files_frame, text="Diretório local:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        
        local_frame = ttk.Frame(files_frame)
        local_frame.grid(row=4, column=1, sticky="ew", padx=5, pady=5)
        
        ttk.Entry(local_frame, textvariable=self.local_output_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(local_frame, text="Procurar", command=self._browse_local_dir).pack(side="left", padx=5)
        
        # Botão para selecionar arquivos R1 e R2 juntos
        ttk.Button(files_frame, text="Selecionar Arquivos R1/R2", command=self._browse_reads).grid(
            row=5, column=0, columnspan=2, pady=10
        )
    
    def _create_params_frame(self):
        """Cria frame de parâmetros do SPAdes"""
        params_frame = ttk.LabelFrame(self, text="Parâmetros do SPAdes")
        params_frame.pack(fill="x", padx=10, pady=5)
        
        # Grid para organizar widgets
        params_frame.columnconfigure(1, weight=1)
        params_frame.columnconfigure(3, weight=1)
        
        # Threads
        ttk.Label(params_frame, text="Threads:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(params_frame, textvariable=self.threads, width=8).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Memória
        ttk.Label(params_frame, text="Memória (GB):").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        ttk.Entry(params_frame, textvariable=self.memory, width=8).grid(row=0, column=3, sticky="w", padx=5, pady=5)
        
        # Modo
        ttk.Label(params_frame, text="Modo:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        from config.settings import SPADES_MODES
        mode_combo = ttk.Combobox(params_frame, textvariable=self.mode, state="readonly", values=SPADES_MODES, width=15)
        mode_combo.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        if not self.mode.get():
            self.mode.set(DEFAULT_MODE)
        
        # K-mer
        ttk.Label(params_frame, text="K-mer (opcional):").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        kmer_frame = ttk.Frame(params_frame)
        kmer_frame.grid(row=1, column=3, sticky="ew", padx=5, pady=5)
        
        ttk.Entry(kmer_frame, textvariable=self.kmer, width=15).pack(side="left")
        ttk.Label(kmer_frame, text="Ex: 21,33,55,77").pack(side="left", padx=5)
    
    def _load_server_profiles(self):
        """Carrega a lista de perfis de servidor"""
        profiles = self.server_profiles.get_profile_names()
        self.profile_combo["values"] = profiles
        
        if profiles:
            self.status_updater.update_log(f"Carregados {len(profiles)} perfis de servidor")
    
    def _on_profile_selected(self, event):
        """Evento chamado quando um perfil é selecionado no combobox"""
        profile_name = self.selected_profile.get()
        if not profile_name:
            return
            
        profile = self.server_profiles.get_profile(profile_name)
        if not profile:
            self.status_updater.update_log(f"Perfil '{profile_name}' não encontrado", "WARNING")
            return
            
        # Preencher campos com os valores do perfil
        self.server_host.set(profile.get("host", ""))
        self.server_port.set(profile.get("port", DEFAULT_PORT))
        self.server_username.set(profile.get("username", ""))
        self.server_password.set(profile.get("password", ""))
        self.ssh_key_path.set(profile.get("key_path", ""))
        self.use_key_auth.set(profile.get("use_key", False))
        
        # Atualizar interface conforme método de autenticação
        self._toggle_auth_method()
        
        self.status_updater.update_log(f"Perfil '{profile_name}' carregado", "SUCCESS")
    
    def _toggle_auth_method(self):
        """Alterna entre autenticação por senha e por chave SSH"""
        if self.use_key_auth.get():
            # Usando chave SSH
            self.password_entry.config(state="disabled")
            self.key_entry.config(state="normal")
            self.key_button.config(state="normal")
        else:
            # Usando senha
            self.password_entry.config(state="normal")
            self.key_entry.config(state="disabled")
            self.key_button.config(state="disabled")
    
    def _browse_ssh_key(self):
        """Abre diálogo para selecionar arquivo de chave SSH"""
        filepath = filedialog.askopenfilename(
            title="Selecione o arquivo de chave SSH",
            filetypes=(
                ("All files", "*.*"),
                ("PEM files", "*.pem"),
                ("Key files", "*.key"),
                ("OpenSSH files", "*.pkey")
            )
        )
        if filepath:
            self.ssh_key_path.set(filepath)
    
    def _browse_file(self, var, title):
        """Abre diálogo para selecionar arquivo"""
        filepath = filedialog.askopenfilename(
            title=title,
            filetypes=(
                ("FASTQ files", "*.fastq;*.fq;*.fastq.gz;*.fq.gz"),
                ("All files", "*.*")
            )
        )
        if filepath:
            var.set(filepath)
    
    def _browse_reads(self):
        """Abre diálogo para selecionar arquivos R1 e R2 em sequência"""
        # Primeiro selecionar R1
        r1 = filedialog.askopenfilename(
            title="Selecione o arquivo R1 (Forward)",
            filetypes=(
                ("FASTQ files", "*.fastq;*.fq;*.fastq.gz;*.fq.gz"),
                ("All files", "*.*")
            )
        )
        
        if not r1:
            return
            
        self.read1_path.set(r1)
        
        # Tentar adivinhar o nome do arquivo R2 a partir do R1
        r1_name = os.path.basename(r1)
        r1_dir = os.path.dirname(r1)
        r2_guess = None
        
        # Padrões comuns: _R1_ -> _R2_, _1. -> _2., _1_ -> _2_
        if "_R1_" in r1_name:
            r2_guess = os.path.join(r1_dir, r1_name.replace("_R1_", "_R2_"))
        elif "_1." in r1_name:
            r2_guess = os.path.join(r1_dir, r1_name.replace("_1.", "_2."))
        elif "_1_" in r1_name:
            r2_guess = os.path.join(r1_dir, r1_name.replace("_1_", "_2_"))
            
        # Se encontrou um candidato a R2 e ele existe, preencher automaticamente
        if r2_guess and os.path.exists(r2_guess):
            self.read2_path.set(r2_guess)
            self.status_updater.update_log(f"Arquivo R2 preenchido automaticamente: {os.path.basename(r2_guess)}")
        else:
            # Senão, pedir para selecionar manualmente
            r2 = filedialog.askopenfilename(
                title="Selecione o arquivo R2 (Reverse)",
                filetypes=(
                    ("FASTQ files", "*.fastq;*.fq;*.fastq.gz;*.fq.gz"),
                    ("All files", "*.*")
                )
            )
            if r2:
                self.read2_path.set(r2)
    
    def _browse_local_dir(self):
        """Abre diálogo para selecionar diretório local para resultados"""
        dirpath = filedialog.askdirectory(title="Selecione o diretório local para resultados")
        if dirpath:
            self.local_output_dir.set(dirpath)
    
    def _new_profile(self):
        """Cria um novo perfil de servidor"""
        # Limpar campos primeiro
        self.selected_profile.set("")
        self.server_host.set("")
        self.server_port.set(DEFAULT_PORT)
        self.server_username.set("")
        self.server_password.set("")
        self.ssh_key_path.set("")
        self.use_key_auth.set(False)
        
        # Mostrar diálogo
        ProfileDialog(self.parent, self.server_profiles, self._profile_saved_callback)
    
    def _save_current_profile(self):
        """Salva o perfil atual"""
        profile_name = self.selected_profile.get()
        
        # Se não há perfil selecionado, mostrar diálogo para novo perfil
        if not profile_name:
            ProfileDialog(self.parent, self.server_profiles, self._profile_saved_callback)
            return
            
        # Verifica se é um perfil existente
        profile = self.server_profiles.get_profile(profile_name)
        if profile:
            # Atualizar perfil existente
            success = self.server_profiles.update_profile(
                profile_name,
                self.server_host.get().strip(),
                self.server_port.get().strip(),
                self.server_username.get().strip(),
                self.server_password.get(),
                self.ssh_key_path.get().strip(),
                self.use_key_auth.get()
            )
            
            if success:
                self.status_updater.update_log(f"Perfil '{profile_name}' atualizado com sucesso", "SUCCESS")
            else:
                self.status_updater.update_log("Erro ao atualizar perfil", "ERROR")
        else:
            # Criar novo perfil com o nome selecionado
            self.status_updater.update_log(f"Perfil '{profile_name}' não encontrado. Criando novo.", "WARNING")
            ProfileDialog(self.parent, self.server_profiles, self._profile_saved_callback, profile_name)
    
    def _profile_saved_callback(self, profile_name=None):
        """Callback chamado quando um perfil é salvo"""
        self._load_server_profiles()
        
        # Selecionar o perfil salvo
        if profile_name:
            self.selected_profile.set(profile_name)
            # Trigger o evento de seleção manualmente
            self._on_profile_selected(None)
    
    def _show_profile_manager(self):
        """Mostra o diálogo de gerenciamento de perfis"""
        ProfileManagerDialog(self.parent, self.server_profiles, self._load_server_profiles)
    
    def _test_connection(self):
        """Testa a conexão com o servidor"""
        # Esta função seria implementada na classe principal que tem acesso ao job_manager
        # Aqui apenas chamamos um evento que será capturado pela classe principal
        self.event_generate("<<TestConnection>>")

    def get_connection_params(self):
        """Retorna os parâmetros de conexão"""
        return {
            "host": self.server_host.get().strip(),
            "port": self.server_port.get().strip(),
            "username": self.server_username.get().strip(),
            "password": self.server_password.get(),
            "key_path": self.ssh_key_path.get().strip(),
            "use_key": self.use_key_auth.get()
        }
        
    def get_spades_params(self):
        """Retorna os parâmetros do SPAdes"""
        return {
            "read1_path": self.read1_path.get(),
            "read2_path": self.read2_path.get(),
            "remote_dir": self.remote_dir.get().strip(),
            "output_dir": self.output_dir.get().strip(),
            "local_output_dir": self.local_output_dir.get().strip(),
            "threads": self.threads.get().strip(),
            "memory": self.memory.get().strip(),
            "mode": self.mode.get(),
            "kmer": self.kmer.get().strip()
        }