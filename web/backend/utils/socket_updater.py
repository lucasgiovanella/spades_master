# WebSocket updater 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Classe para atualizar status e logs via WebSockets
Substitui a classe status_updater.py original para comunicação web
"""

import queue
import threading
import time
from datetime import datetime
from flask_socketio import emit
from backend.app import socketio
from backend.utils.logging_utils import log_info, log_warning, log_error, log_success

class SocketUpdater:
    """Classe para atualizar status e logs via WebSockets"""
    def __init__(self, namespace='/logs'):
        self.namespace = namespace
        self.queue = queue.Queue()
        self.running = True
        self.thread = None
        
    def start(self):
        """Inicia o processamento da fila em uma thread separada"""
        if self.thread is None or not self.thread.is_alive():
            self.running = True
            self.thread = threading.Thread(target=self._process_queue, daemon=True)
            self.thread.start()
            
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
            
        self.queue.put(("log", {
            'message': formatted_text,
            'level': level,
            'raw_message': text,
            'timestamp': timestamp
        }))
        
    def update_progress(self, value):
        """Atualiza o valor da barra de progresso"""
        self.queue.put(("progress", value))
    
    def update_server_info(self, info):
        """Atualiza informações do servidor"""
        self.queue.put(("server_info", info))
    
    def update_job_status(self, status):
        """Atualiza o status do job atual"""
        self.queue.put(("job_status", status))
    
    def update_metrics(self, metrics):
        """Atualiza métricas do servidor (CPU, memória, etc.)"""
        self.queue.put(("metrics", metrics))
    
    def _process_queue(self):
        """Processa a fila de mensagens"""
        while self.running:
            try:
                msg_type, msg = self.queue.get(timeout=0.1)
                
                # Enviar via websocket para clientes conectados
                with socketio.test_request_context('/'):
                    if msg_type == "status":
                        socketio.emit('status_update', {'message': msg}, namespace=self.namespace)
                    elif msg_type == "log":
                        socketio.emit('log_message', msg, namespace=self.namespace)
                    elif msg_type == "progress":
                        socketio.emit('progress_update', {'value': msg}, namespace=self.namespace)
                    elif msg_type == "server_info":
                        socketio.emit('server_info', msg, namespace=self.namespace)
                    elif msg_type == "job_status":
                        socketio.emit('job_status', msg, namespace=self.namespace)
                    elif msg_type == "metrics":
                        socketio.emit('metrics_update', msg, namespace=self.namespace)
                
                self.queue.task_done()
            except queue.Empty:
                pass
            except Exception as e:
                print(f"Erro ao processar mensagem na fila: {str(e)}")
            
    def stop(self):
        """Para o processamento da fila"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None