#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Launcher para a aplicação SPAdes Master Web
Quando executado como aplicativo standalone, este script:
1. Inicia o servidor web em background
2. Exibe instruções no terminal
3. Abre o navegador com a interface web
"""

import os
import sys
import platform
import subprocess
import webbrowser
import signal
import time
import random
import socket

# Título ASCII art para o terminal
TITLE = """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███████╗██████╗  █████╗ ██████╗ ███████╗███████╗           ║
║   ██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝           ║
║   ███████╗██████╔╝███████║██║  ██║█████╗  ███████╗           ║
║   ╚════██║██╔═══╝ ██╔══██║██║  ██║██╔══╝  ╚════██║           ║
║   ███████║██║     ██║  ██║██████╔╝███████╗███████║           ║
║   ╚══════╝╚═╝     ╚═╝  ╚═╝╚═════╝ ╚══════╝╚══════╝           ║
║                                                               ║
║   ███╗   ███╗ █████╗ ███████╗████████╗███████╗██████╗        ║
║   ████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗       ║
║   ██╔████╔██║███████║███████╗   ██║   █████╗  ██████╔╝       ║
║   ██║╚██╔╝██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗       ║
║   ██║ ╚═╝ ██║██║  ██║███████║   ██║   ███████╗██║  ██║       ║
║   ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝       ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""

def find_available_port(start=5000, end=5050):
    """Encontra uma porta disponível no sistema"""
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    return start  # Fallback para a porta padrão se não encontrar disponível

def clear_screen():
    """Limpa a tela do terminal"""
    if platform.system() == "Windows":
        os.system('cls')
    else:
        os.system('clear')

def print_instructions(url):
    """Imprime instruções no terminal"""
    clear_screen()
    print(TITLE)
    print("\nBem-vindo ao SPAdes Master Web!\n")
    print(f"O servidor está rodando em: \033[1;34m{url}\033[0m")
    print("\nInstruções:")
    print("  1. A interface web foi aberta automaticamente no seu navegador")
    print("  2. Caso não abra, copie e cole o URL acima no seu navegador")
    print("  3. Para encerrar, pressione Ctrl+C neste terminal ou feche a janela")
    print("\nAguardando conexões...\n")

def main():
    """Função principal para iniciar o aplicativo"""
    # Encontrar porta disponível
    port = find_available_port()
    host = '127.0.0.1'
    url = f"http://{host}:{port}"
    
    try:
        # Iniciar servidor em um processo separado
        server_process = subprocess.Popen(
            [sys.executable, "app.py", "--host", host, "--port", str(port), "--no-browser"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Esperar um pouco para o servidor inicializar
        time.sleep(1.5)
        
        # Verificar se o servidor iniciou corretamente
        if server_process.poll() is not None:
            print("Erro ao iniciar o servidor. Verifique as dependências e tente novamente.")
            return
        
        # Abrir o navegador
        webbrowser.open(url)
        
        # Exibir instruções
        print_instructions(url)
        
        # Manter o processo rodando até Ctrl+C
        while True:
            if server_process.poll() is not None:
                print("\nO servidor foi encerrado.")
                break
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nEncerrando SPAdes Master Web...")
        if 'server_process' in locals():
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server_process.kill()
        print("Aplicação encerrada. Até logo!")

if __name__ == "__main__":
    main()