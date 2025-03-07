# SSH utilities 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitários para operações SSH no SPAdes Master Web
"""

import os
import socket
import subprocess
import platform
import threading
import time
from pathlib import Path
import paramiko
from utils.logging_utils import log_info, log_error, log_warning

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
            subprocess.Popen(full_command, shell=True)
            log_info(f"Terminal SSH aberto no Windows para {username}@{host}")
        elif platform.system() == "Darwin":  # macOS
            # No macOS, abrir Terminal.app
            applescript = f'tell app "Terminal" to do script "{ssh_command}"'
            subprocess.run(["osascript", "-e", applescript])
            log_info(f"Terminal SSH aberto no macOS para {username}@{host}")
        else:  # Linux/Unix
            # No Linux, tentar abrir terminal padrão
            # Tentar vários terminais comuns
            terminals = ["gnome-terminal", "xterm", "konsole", "xfce4-terminal", "terminator", "tilix"]
            
            for term in terminals:
                try:
                    subprocess.Popen([term, "-e", ssh_command])
                    log_info(f"Terminal SSH ({term}) aberto no Linux para {username}@{host}")
                    return True
                except FileNotFoundError:
                    continue
                    
            # Se nenhum terminal for encontrado, tentar com x-terminal-emulator
            try:
                subprocess.Popen(["x-terminal-emulator", "-e", ssh_command])
                log_info(f"Terminal SSH (x-terminal-emulator) aberto para {username}@{host}")
                return True
            except FileNotFoundError:
                log_error("Nenhum terminal encontrado no sistema Linux")
                return False
            
        return True
    except Exception as e:
        log_error(f"Erro ao abrir terminal SSH: {str(e)}")
        return False

def verify_ssh_connection(ssh_client):
    """
    Verifica se a conexão SSH está ativa
    
    Args:
        ssh_client: Cliente SSH (paramiko.SSHClient)
        
    Returns:
        bool: True se a conexão está ativa
    """
    if not ssh_client:
        return False
        
    transport = ssh_client.get_transport()
    return transport and transport.is_active()

def check_directory_exists(ssh_client, path):
    """
    Verifica se um diretório existe no servidor remoto
    
    Args:
        ssh_client: Cliente SSH (paramiko.SSHClient)
        path: Caminho do diretório a verificar
        
    Returns:
        bool: True se o diretório existe
    """
    try:
        if not verify_ssh_connection(ssh_client):
            return False
            
        stdin, stdout, stderr = ssh_client.exec_command(f"[ -d \"{path}\" ] && echo 'EXISTS' || echo 'NOT_EXISTS'")
        result = stdout.read().decode().strip()
        
        return result == 'EXISTS'
    except Exception as e:
        log_error(f"Erro ao verificar diretório: {str(e)}")
        return False

def check_file_exists(ssh_client, path):
    """
    Verifica se um arquivo existe no servidor remoto
    
    Args:
        ssh_client: Cliente SSH (paramiko.SSHClient)
        path: Caminho do arquivo a verificar
        
    Returns:
        bool: True se o arquivo existe
    """
    try:
        if not verify_ssh_connection(ssh_client):
            return False
            
        stdin, stdout, stderr = ssh_client.exec_command(f"[ -f \"{path}\" ] && echo 'EXISTS' || echo 'NOT_EXISTS'")
        result = stdout.read().decode().strip()
        
        return result == 'EXISTS'
    except Exception as e:
        log_error(f"Erro ao verificar arquivo: {str(e)}")
        return False

def create_directory(ssh_client, path):
    """
    Cria um diretório no servidor remoto
    
    Args:
        ssh_client: Cliente SSH (paramiko.SSHClient)
        path: Caminho do diretório a criar
        
    Returns:
        bool: True se o diretório foi criado com sucesso
    """
    try:
        if not verify_ssh_connection(ssh_client):
            return False
            
        stdin, stdout, stderr = ssh_client.exec_command(f"mkdir -p \"{path}\" && echo 'SUCCESS' || echo 'FAILED'")
        result = stdout.read().decode().strip()
        
        return result == 'SUCCESS'
    except Exception as e:
        log_error(f"Erro ao criar diretório: {str(e)}")
        return False

def get_file_size(ssh_client, path):
    """
    Obtém o tamanho de um arquivo no servidor remoto
    
    Args:
        ssh_client: Cliente SSH (paramiko.SSHClient)
        path: Caminho do arquivo
        
    Returns:
        int: Tamanho do arquivo em bytes ou None se ocorrer erro
    """
    try:
        if not verify_ssh_connection(ssh_client):
            return None
            
        stdin, stdout, stderr = ssh_client.exec_command(f"stat -c %s \"{path}\" 2>/dev/null || echo 'ERROR'")
        result = stdout.read().decode().strip()
        
        if result == 'ERROR' or not result.isdigit():
            return None
            
        return int(result)
    except Exception as e:
        log_error(f"Erro ao obter tamanho do arquivo: {str(e)}")
        return None

def get_file_content(ssh_client, path, max_size=10*1024*1024):
    """
    Obtém o conteúdo de um arquivo no servidor remoto
    
    Args:
        ssh_client: Cliente SSH (paramiko.SSHClient)
        path: Caminho do arquivo
        max_size: Tamanho máximo em bytes para ler (padrão: 10MB)
        
    Returns:
        str: Conteúdo do arquivo ou None se ocorrer erro
    """
    try:
        if not verify_ssh_connection(ssh_client):
            return None
            
        # Verificar tamanho do arquivo
        file_size = get_file_size(ssh_client, path)
        if file_size is None:
            log_warning(f"Não foi possível obter o tamanho do arquivo: {path}")
            return None
            
        if file_size > max_size:
            log_warning(f"Arquivo muito grande para ser lido: {file_size/1024/1024:.2f} MB")
            return None
            
        # Ler conteúdo
        stdin, stdout, stderr = ssh_client.exec_command(f"cat \"{path}\" 2>/dev/null")
        content = stdout.read().decode('utf-8', errors='replace')
        
        return content
    except Exception as e:
        log_error(f"Erro ao ler conteúdo do arquivo: {str(e)}")
        return None

def execute_command_with_timeout(ssh_client, command, timeout=30):
    """
    Executa um comando no servidor remoto com timeout
    
    Args:
        ssh_client: Cliente SSH (paramiko.SSHClient)
        command: Comando a ser executado
        timeout: Tempo máximo em segundos para execução
        
    Returns:
        tuple: (success, stdout, stderr) onde success é um boolean
    """
    try:
        if not verify_ssh_connection(ssh_client):
            return False, "", "Conexão SSH inativa"
            
        # Criar objeto Channel para poder definir timeout
        transport = ssh_client.get_transport()
        channel = transport.open_session()
        channel.settimeout(timeout)
        
        # Executar comando
        channel.exec_command(command)
        
        # Coletar saída
        stdout_data = channel.recv(1024*1024).decode('utf-8', errors='replace')
        stderr_data = channel.recv_stderr(1024*1024).decode('utf-8', errors='replace')
        
        # Verificar status de saída
        exit_status = channel.recv_exit_status()
        success = exit_status == 0
        
        return success, stdout_data, stderr_data
    except socket.timeout:
        return False, "", f"Timeout ao executar comando (limite: {timeout}s)"
    except Exception as e:
        log_error(f"Erro ao executar comando: {str(e)}")
        return False, "", str(e)

def find_executable(ssh_client, executable_name, search_paths=None):
    """
    Procura um executável no servidor remoto
    
    Args:
        ssh_client: Cliente SSH (paramiko.SSHClient)
        executable_name: Nome do executável
        search_paths: Lista de diretórios para procurar (opcional)
        
    Returns:
        str: Caminho completo do executável ou None se não encontrado
    """
    try:
        if not verify_ssh_connection(ssh_client):
            return None
            
        # Primeira tentativa: usar comando which
        stdin, stdout, stderr = ssh_client.exec_command(f"which {executable_name} 2>/dev/null || echo 'NOT_FOUND'")
        path = stdout.read().decode().strip()
        
        if path != 'NOT_FOUND':
            return path
            
        # Segunda tentativa: verificar caminhos específicos
        if search_paths:
            for base_path in search_paths:
                # Expandir ~/ se presente
                if base_path.startswith('~/'):
                    stdin, stdout, stderr = ssh_client.exec_command("echo $HOME")
                    home = stdout.read().decode().strip()
                    path = base_path.replace('~', home)
                else:
                    path = base_path
                    
                # Verificar se o caminho existe e é executável
                full_path = f"{path}/{executable_name}" if not path.endswith(executable_name) else path
                stdin, stdout, stderr = ssh_client.exec_command(f"[ -f {full_path} ] && [ -x {full_path} ] && echo '{full_path}' || echo 'NOT_FOUND'")
                result = stdout.read().decode().strip()
                
                if result != 'NOT_FOUND':
                    return result
                    
        return None
    except Exception as e:
        log_error(f"Erro ao procurar executável: {str(e)}")
        return None