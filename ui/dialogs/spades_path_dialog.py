#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox

class SpadesPathDialog:
    """Diálogo para especificar o caminho do SPAdes manualmente"""
    def __init__(self, parent, job_manager, status_updater):
        """
        Inicializa o diálogo
        
        Args:
            parent: Widget pai
            job_manager: Instância do JobManager
            status_updater: Instância do StatusUpdater
        """
        self.parent = parent
        self.job_manager = job_manager
        self.status_updater = status_updater
        self.path = tk.StringVar()
        self.result = False
        
        # Criar janela
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Especificar Caminho do SPAdes")
        self.dialog.geometry("600x250")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centralizar no pai
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Criar widgets
        self._create_widgets()
        
        # Definir como modal
        self.dialog.wait_window()
        
    def _create_widgets(self):
        """Cria os widgets do diálogo"""
        frame = ttk.Frame(self.dialog, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Mensagem
        message = ttk.Label(
            frame, 
            text="SPAdes não foi encontrado automaticamente no servidor.\n"
                 "Por favor, especifique o caminho completo do executável SPAdes:",
            wraplength=550,
            justify=tk.LEFT
        )
        message.pack(fill=tk.X, pady=(0, 20))
        
        # Entrada de caminho
        path_frame = ttk.Frame(frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(path_frame, text="Caminho do SPAdes:").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Entry(path_frame, textvariable=self.path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Sugestões
        suggestions_frame = ttk.LabelFrame(frame, text="Caminhos comuns")
        suggestions_frame.pack(fill=tk.X, pady=15)
        
        from config.settings import COMMON_SPADES_PATHS
        for i, path in enumerate(COMMON_SPADES_PATHS):
            if i < 5:  # Mostrar apenas os primeiros 5 caminhos
                btn = ttk.Button(
                    suggestions_frame, 
                    text=path,
                    command=lambda p=path: self.path.set(p)
                )
                btn.pack(anchor=tk.W, padx=5, pady=2)
        
        # Botões
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))
        
        ttk.Button(
            button_frame, 
            text="Verificar e Salvar", 
            command=self._verify_path
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            button_frame, 
            text="Cancelar", 
            command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
    def _verify_path(self):
        """Verifica se o caminho informado é válido"""
        path = self.path.get().strip()
        
        if not path:
            messagebox.showerror("Erro", "Por favor, informe o caminho do SPAdes.")
            return
            
        # Verificar se o caminho é válido no servidor
        if not self.job_manager.ssh:
            messagebox.showerror("Erro", "Não há conexão ativa com o servidor.")
            self.dialog.destroy()
            return
            
        try:
            # Verificar se o arquivo existe e é executável
            stdin, stdout, stderr = self.job_manager.ssh.exec_command(
                f"[ -f {path} ] && [ -x {path} ] && echo 'OK' || echo 'NOT_FOUND'"
            )
            result = stdout.read().decode().strip()
            
            if result == 'OK':
                # Verificar se é realmente o SPAdes
                stdin, stdout, stderr = self.job_manager.ssh.exec_command(f"{path} --version")
                version = stdout.read().decode().strip()
                
                if "SPAdes" in version:
                    self.job_manager.spades_path = path
                    self.status_updater.update_log(f"SPAdes encontrado: {path}", "SUCCESS")
                    self.status_updater.update_log(f"Versão do SPAdes: {version}", "SUCCESS")
                    self.result = True
                    messagebox.showinfo("Sucesso", f"SPAdes encontrado!\nVersão: {version}")
                    self.dialog.destroy()
                else:
                    messagebox.showerror(
                        "Erro", 
                        "O arquivo especificado não parece ser o SPAdes.\n"
                        f"Saída do comando: {version}"
                    )
            else:
                messagebox.showerror(
                    "Erro", 
                    "Arquivo não encontrado ou não tem permissão de execução.\n"
                    "Verifique o caminho e tente novamente."
                )
                
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao verificar o caminho:\n{str(e)}")