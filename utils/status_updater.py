#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
import threading
import queue
from datetime import datetime
from utils.logging_utils import log_info, log_warning, log_error, log_success

class StatusUpdater:
    """Classe para atualizar status e logs de forma thread-safe"""
    def __init__(self, status_var, log_text, progress_var=None):
        self.status_var = status_var
        self.log_text = log_text
        self.progress_var = progress_var
        self.queue = queue.Queue()
        self.running = True
        
    def start(self):
        """Inicia o processamento da fila em uma thread separada"""
        threading.Thread(target=self._process_queue, daemon=True).start()
        
    def update_status(self, text):
        """Atualiza o texto de status"""
        self.queue.put(("status", text))
        log_info(f"Status: {text}")
        
    def update_log(self, text, level="INFO"):
        """Adiciona uma entrada ao log com o nível especificado"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if level == "ERROR":
            formatted_text = f"[{timestamp}] [ERRO] {text}"
            log_error(text)
        elif level == "WARNING":
            formatted_text = f"[{timestamp}] [AVISO] {text}"
            log_warning(text)
        elif level == "SUCCESS":
            formatted_text = f"[{timestamp}] [SUCESSO] {text}"
            log_success(text)
        else:
            formatted_text = f"[{timestamp}] [INFO] {text}"
            log_info(text)
            
        self.queue.put(("log", formatted_text))
        
    def update_progress(self, value):
        """Atualiza o valor da barra de progresso"""
        if self.progress_var is not None:
            self.queue.put(("progress", value))
    
    def _process_queue(self):
        """Processa a fila de mensagens"""
        while self.running:
            try:
                msg_type, msg = self.queue.get(timeout=0.1)
                
                if msg_type == "status":
                    self.status_var.set(msg)
                elif msg_type == "log" and self.log_text is not None:
                    self.log_text.configure(state='normal')
                    
                    # Aplicar cores com base no nível de log
                    if "[ERRO]" in msg:
                        self.log_text.tag_configure("error", foreground="red")
                        self.log_text.insert(tk.END, msg + "\n", "error")
                    elif "[AVISO]" in msg:
                        self.log_text.tag_configure("warning", foreground="orange")
                        self.log_text.insert(tk.END, msg + "\n", "warning")
                    elif "[SUCESSO]" in msg:
                        self.log_text.tag_configure("success", foreground="green")
                        self.log_text.insert(tk.END, msg + "\n", "success")
                    else:
                        self.log_text.insert(tk.END, msg + "\n")
                    
                    # Rolar para o final
                    self.log_text.see(tk.END)
                    self.log_text.configure(state='disabled')
                elif msg_type == "progress":
                    self.progress_var.set(msg)
                
                self.queue.task_done()
            except queue.Empty:
                pass
            except Exception as e:
                print(f"Erro ao processar mensagem na fila: {str(e)}")
            
    def stop(self):
        """Para o processamento da fila"""
        self.running = False