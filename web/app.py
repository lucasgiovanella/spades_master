# Flask application 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Ponto de entrada principal da aplicação web SPAdes Master
"""

import os
import argparse
import webbrowser
import threading
import time
import eventlet
eventlet.monkey_patch()
from backend.app import create_app, socketio

def open_browser(host, port, wait=1.0):
    """Abre o navegador após um curto intervalo"""
    time.sleep(wait)  # Espera um pouco para o servidor iniciar
    url = f"http://{host}:{port}"
    print(f"Abrindo o navegador em: {url}")
    webbrowser.open(url)

def main():
    """Função principal para iniciar a aplicação web"""
    parser = argparse.ArgumentParser(description='SPAdes Master Web')
    parser.add_argument('--host', default='127.0.0.1', help='Host para o servidor web')
    parser.add_argument('--port', default=5000, type=int, help='Porta para o servidor web')
    parser.add_argument('--no-browser', action='store_true', help='Não abrir o navegador automaticamente')
    parser.add_argument('--debug', action='store_true', help='Executar em modo debug')
    
    args = parser.parse_args()
    
    # Inicializar diretórios necessários
    os.makedirs('temp', exist_ok=True)
    
    app = create_app()
    
    # Configurar host e porta
    host = args.host
    port = args.port
    
    # Abrir navegador automaticamente (a menos que --no-browser seja especificado)
    if not args.no_browser:
        threading.Thread(target=open_browser, args=(host, port), daemon=True).start()
    
    # Iniciar o servidor Flask com socketio
    print(f"Iniciando SPAdes Master Web em http://{host}:{port}")
    print("Pressione Ctrl+C para encerrar")
    
    socketio.run(app, host=host, port=port, debug=args.debug)

if __name__ == "__main__":
    main()