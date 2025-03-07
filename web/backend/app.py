#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Aplicação Flask principal para o SPAdes Master Web
"""

import os
from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO

# Configurações globais
from config.settings import APP_VERSION, APP_NAME

# Inicializar socketio para atualizações em tempo real
socketio = SocketIO()

def create_app(test_config=None):
    """Cria e configura a aplicação Flask"""
    # Criar e configurar a app
    app = Flask(__name__, 
                static_folder='../frontend/static',
                template_folder='../frontend/templates')
    
    # Configurações básicas
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key_replace_in_production'),
        APP_NAME=APP_NAME,
        APP_VERSION=APP_VERSION,
    )

    # Registrar blueprints para os diferentes módulos da API
    from backend.api.server_profiles import bp as profiles_bp
    from backend.api.execution import bp as execution_bp
    from backend.api.results import bp as results_bp
    
    app.register_blueprint(profiles_bp)
    app.register_blueprint(execution_bp)
    app.register_blueprint(results_bp)
    
    # Inicializar Socket.IO com a aplicação
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Garantir que os diretórios necessários existam
    from config.settings import ensure_dirs_exist
    ensure_dirs_exist()
    
    # Rota principal
    @app.route('/')
    def index():
        """Página inicial"""
        return render_template('dashboard.html')
    
    # Rotas para as diferentes seções
    @app.route('/profiles')
    def profiles():
        """Página de perfis de servidor"""
        return render_template('profiles.html')
    
    @app.route('/execution')
    def execution():
        """Página de execução e monitoramento"""
        return render_template('execution.html')
    
    @app.route('/results')
    def results():
        """Página de resultados"""
        return render_template('results.html')
    
    # Rota de status
    @app.route('/api/status')
    def status():
        """Endpoint para verificar status da API"""
        return jsonify({
            'status': 'online',
            'app_name': APP_NAME,
            'version': APP_VERSION
        })
    
    return app