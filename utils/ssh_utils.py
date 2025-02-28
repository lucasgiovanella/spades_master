#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import subprocess
import platform

def generate_ssh_command(host, port, username, key_path=None):
    """
    Gera o comando SSH apropriado para conexão manual
    
    Args:
        host: Endereço do servidor
        port: Porta SSH
        username: Nome de usuário
        key_path: Caminho para a chave privada (opcional)
        
    Returns:
        str: Comando SSH formatado corretamente
    """
    # Iniciar com o comando base
    command = "ssh"
    
    # Adicionar opção de porta se não for a padrão
    if port and port != "22":
        command += f" -p {port}"
    
    # Adicionar caminho da chave se fornecido
    if key_path and os.path.exists(key_path):
        command += f" -i \"{key_path}\""
        
    # Adicionar user@host
    command += f" {username}@{host}"
    
    return command

def open_ssh_terminal(host, port, username, key_path=None):
    """
    Abre um terminal com o comando SSH pronto para conexão
    
    Args:
        host: Endereço do servidor
        port: Porta SSH
        username: Nome de usuário
        key_path: Caminho para a chave privada (opcional)
        
    Returns:
        bool: True se o terminal foi aberto com sucesso
    """
    try:
        ssh_command = generate_ssh_command(host, port, username, key_path)
        
        # Abrir terminal adequado ao sistema operacional
        if platform.system() == "Windows":
            # No Windows, abrir CMD com o comando
            full_command = f"cmd.exe /K \"{ssh_command}\""
            subprocess.Popen(full_command)
        elif platform.system() == "Darwin":  # macOS
            # No macOS, abrir Terminal.app
            applescript = f'tell app "Terminal" to do script "{ssh_command}"'
            subprocess.run(["osascript", "-e", applescript])
        else:  # Linux/Unix
            # No Linux, tentar abrir terminal padrão
            # Tentar vários terminais comuns
            terminals = ["gnome-terminal", "xterm", "konsole", "xfce4-terminal"]
            
            for term in terminals:
                try:
                    subprocess.Popen([term, "-e", ssh_command])
                    return True
                except FileNotFoundError:
                    continue
                    
            # Se nenhum terminal for encontrado
            return False
            
        return True
    except Exception:
        return False