#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

class ProfileDialog:
    """Diálogo para adicionar ou editar perfil de servidor"""
    def __init__(self, parent, server_profiles, callback, profile_name=None):
        """
        Inicializa o diálogo de perfil
        
        Args:
            parent: Widget pai
            server_profiles: Instância de ServerProfile
            callback: Função a ser chamada após salvar
            profile_name: Nome do perfil a ser editado (None para novo)
        """
        self.parent = parent
        self.server_profiles = server_profiles
        self.callback = callback
        self.editing_profile = profile_name
        
        # Criar janela de diálogo
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Adicionar Perfil" if not profile_name else f"Editar Perfil: {profile_name}")
        self.dialog.geometry("700x600")  # Aumentada a largura de 500 para 700
        self.dialog.transient(parent)
        self.dialog.grab_set()
        self.dialog.resizable(True, True)  # Permitir redimensionamento
        
        # Centralizar no pai
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Variáveis
        self.profile_name_var = tk.StringVar()
        self.host_var = tk.StringVar()
        self.port_var = tk.StringVar(value="22")
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.key_path_var = tk.StringVar()
        self.use_key_var = tk.BooleanVar(value=False)
        
        # Carregar dados se estiver editando
        if profile_name:
            self._load_profile(profile_name)
        
        # Criar widgets
        self._create_widgets()
        
    def _load_profile(self, profile_name):
        """Carrega dados do perfil para edição"""
        profile = self.server_profiles.get_profile(profile_name)
        if profile:
            self.profile_name_var.set(profile_name)
            self.host_var.set(profile.get("host", ""))
            self.port_var.set(profile.get("port", "22"))
            self.username_var.set(profile.get("username", ""))
            self.password_var.set(profile.get("password", ""))
            self.key_path_var.set(profile.get("key_path", ""))
            self.use_key_var.set(profile.get("use_key", False))
    
    def _create_widgets(self):
        """Cria os widgets do diálogo"""
        # Usar Canvas com Scrollbar para garantir que todo conteúdo seja acessível
        canvas = tk.Canvas(self.dialog)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        
        # Frame principal que conterá todos os widgets
        main_frame = ttk.Frame(canvas)
        
        # Configurar scrolling
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack dos elementos principais
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Criar janela no canvas
        canvas.create_window((0, 0), window=main_frame, anchor="nw", width=680)  # Aumentada a largura
        
        # Frame com padding para os widgets
        frame = ttk.Frame(main_frame, padding="20 20 20 20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Nome do perfil
        ttk.Label(frame, text="Nome do Perfil:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        name_entry = ttk.Entry(frame, textvariable=self.profile_name_var, width=40)  # Aumentada a largura do campo
        name_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Se estiver editando, desabilitar a mudança de nome
        if self.editing_profile:
            name_entry.config(state="disabled")
        
        # Separador
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Servidor
        ttk.Label(frame, text="Endereço do Servidor:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        host_entry = ttk.Entry(frame, textvariable=self.host_var, width=40)  # Aumentada a largura do campo
        host_entry.grid(row=2, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Porta
        ttk.Label(frame, text="Porta:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        port_entry = ttk.Entry(frame, textvariable=self.port_var, width=10)
        port_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Usuário
        ttk.Label(frame, text="Usuário:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        username_entry = ttk.Entry(frame, textvariable=self.username_var, width=40)  # Aumentada a largura do campo
        username_entry.grid(row=4, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Separador
        ttk.Separator(frame, orient=tk.HORIZONTAL).grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Método de autenticação
        auth_frame = ttk.LabelFrame(frame, text="Método de Autenticação", padding=10)
        auth_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Configurar colunas do auth_frame para melhor layout
        auth_frame.columnconfigure(1, weight=1)
        
        # Senha
        password_radio = ttk.Radiobutton(
            auth_frame, 
            text="Usar Senha", 
            variable=self.use_key_var, 
            value=False,
            command=self._toggle_auth_method
        )
        password_radio.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(auth_frame, text="Senha:").grid(row=1, column=0, sticky=tk.W, padx=20, pady=5)
        self.password_entry = ttk.Entry(auth_frame, textvariable=self.password_var, width=40, show="*")  # Aumentada a largura
        self.password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Chave SSH
        key_radio = ttk.Radiobutton(
            auth_frame, 
            text="Usar Chave SSH", 
            variable=self.use_key_var, 
            value=True,
            command=self._toggle_auth_method
        )
        key_radio.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(auth_frame, text="Arquivo de Chave:").grid(row=3, column=0, sticky=tk.W, padx=20, pady=5)
        self.key_entry = ttk.Entry(auth_frame, textvariable=self.key_path_var, width=40)  # Aumentada a largura
        self.key_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        self.key_button = ttk.Button(auth_frame, text="Procurar", command=self._browse_key_file)
        self.key_button.grid(row=3, column=2, padx=5, pady=5)
        
        # Atualizar estado inicial
        self._toggle_auth_method()
        
        # Botões
        button_frame = ttk.Frame(frame)
        button_frame.grid(row=7, column=0, columnspan=3, pady=20)
        
        ttk.Button(button_frame, text="Salvar", command=self._save_profile, width=10).grid(row=0, column=0, padx=10)
        ttk.Button(button_frame, text="Cancelar", command=self.dialog.destroy, width=10).grid(row=0, column=1, padx=10)
        
        # Configurar o scroll do canvas
        def _on_frame_configure(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))
            
        main_frame.bind("<Configure>", _on_frame_configure)
        
        # Permitir scroll com a roda do mouse
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Garantir que o canvas tenha a altura mínima necessária
        main_frame.update_idletasks()
        canvas.config(width=680, height=580)
    
    def _toggle_auth_method(self):
        """Alterna entre métodos de autenticação"""
        if self.use_key_var.get():
            # Usando chave SSH
            self.password_entry.config(state="disabled")
            self.key_entry.config(state="normal")
            self.key_button.config(state="normal")
        else:
            # Usando senha
            self.password_entry.config(state="normal")
            self.key_entry.config(state="disabled")
            self.key_button.config(state="disabled")
    
    def _browse_key_file(self):
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
            self.key_path_var.set(filepath)
    
    def _save_profile(self):
        """Salva o perfil"""
        # Validar campos obrigatórios
        profile_name = self.profile_name_var.get().strip()
        host = self.host_var.get().strip()
        port = self.port_var.get().strip()
        username = self.username_var.get().strip()
        
        # Validações
        if not profile_name:
            messagebox.showerror("Erro", "O nome do perfil é obrigatório.")
            return
            
        if not host:
            messagebox.showerror("Erro", "O endereço do servidor é obrigatório.")
            return
            
        if not username:
            messagebox.showerror("Erro", "O nome de usuário é obrigatório.")
            return
            
        # Validar método de autenticação
        if self.use_key_var.get():
            key_path = self.key_path_var.get().strip()
            if not key_path:
                messagebox.showerror("Erro", "O arquivo de chave SSH é obrigatório.")
                return
            if not os.path.isfile(key_path):
                messagebox.showerror("Erro", f"Arquivo de chave não encontrado: {key_path}")
                return
        else:
            password = self.password_var.get()
            if not password:
                messagebox.showerror("Erro", "A senha é obrigatória quando não se usa chave SSH.")
                return
        
        # Tentar salvar o perfil
        try:
            if self.editing_profile:
                # Atualizar perfil existente
                success = self.server_profiles.update_profile(
                    profile_name,
                    host,
                    port,
                    username,
                    self.password_var.get(),
                    self.key_path_var.get().strip(),
                    self.use_key_var.get()
                )
            else:
                # Criar novo perfil
                success = self.server_profiles.add_profile(
                    profile_name,
                    host,
                    port,
                    username,
                    self.password_var.get(),
                    self.key_path_var.get().strip(),
                    self.use_key_var.get()
                )
                
            if success:
                messagebox.showinfo("Sucesso", f"Perfil '{profile_name}' salvo com sucesso.")
                self.callback(profile_name)  # Chamar callback com o nome do perfil
                self.dialog.destroy()
            else:
                messagebox.showerror("Erro", "Não foi possível salvar o perfil. Verifique o log para mais detalhes.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar perfil: {str(e)}")


class ProfileManagerDialog:
    """Diálogo para gerenciar perfis de servidor"""
    def __init__(self, parent, server_profiles, callback):
        """
        Inicializa o diálogo de gerenciamento de perfis
        
        Args:
            parent: Widget pai
            server_profiles: Instância de ServerProfile
            callback: Função a ser chamada após modificações
        """
        self.parent = parent
        self.server_profiles = server_profiles
        self.callback = callback
        
        # Criar janela
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Gerenciar Perfis de Servidor")
        self.dialog.geometry("600x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Criar widgets
        self._create_widgets()
        
        # Carregar perfis
        self._load_profiles()
        
    def _create_widgets(self):
        """Cria os widgets do diálogo"""
        frame = ttk.Frame(self.dialog, padding="20 20 20 20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Lista de perfis
        list_frame = ttk.LabelFrame(frame, text="Perfis Disponíveis")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Lista com scrollbar
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.profiles_list = tk.Listbox(list_container, width=40, height=10)
        self.profiles_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container, orient=tk.VERTICAL, command=self.profiles_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.profiles_list.config(yscrollcommand=scrollbar.set)
        
        # Botões
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Button(button_frame, text="Adicionar", command=self._add_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Editar", command=self._edit_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Excluir", command=self._delete_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Fechar", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def _load_profiles(self):
        """Carrega a lista de perfis"""
        self.profiles_list.delete(0, tk.END)
        for profile in self.server_profiles.get_profile_names():
            self.profiles_list.insert(tk.END, profile)
    
    def _add_profile(self):
        """Abre diálogo para adicionar novo perfil"""
        ProfileDialog(self.dialog, self.server_profiles, self._on_profile_saved)
    
    def _edit_profile(self):
        """Abre diálogo para editar perfil selecionado"""
        selection = self.profiles_list.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um perfil para editar.")
            return
            
        profile_name = self.profiles_list.get(selection[0])
        ProfileDialog(self.dialog, self.server_profiles, self._on_profile_saved, profile_name)
    
    def _delete_profile(self):
        """Exclui o perfil selecionado"""
        selection = self.profiles_list.curselection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione um perfil para excluir.")
            return
            
        profile_name = self.profiles_list.get(selection[0])
        if messagebox.askyesno("Confirmar", f"Deseja realmente excluir o perfil '{profile_name}'?"):
            success = self.server_profiles.delete_profile(profile_name)
            if success:
                self._load_profiles()
                self.callback()
            else:
                messagebox.showerror("Erro", "Não foi possível excluir o perfil.")
    
    def _on_profile_saved(self, profile_name=None):
        """Callback chamado quando um perfil é salvo"""
        self._load_profiles()
        self.callback()
        
        # Selecionar o perfil salvo, se informado
        if profile_name:
            profiles = self.server_profiles.get_profile_names()
            if profile_name in profiles:
                index = profiles.index(profile_name)
                self.profiles_list.selection_clear(0, tk.END)
                self.profiles_list.selection_set(index)
                self.profiles_list.see(index)