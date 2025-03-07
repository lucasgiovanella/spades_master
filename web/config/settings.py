#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Configurações globais para SPAdes Master Web
"""

import os

# Informações da aplicação
APP_NAME = "SPAdes Master Web"
APP_VERSION = "1.0.0"

# Diretórios da aplicação
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMP_DIR = os.path.join(BASE_DIR, 'temp')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# Arquivo de perfis
PROFILES_FILE = os.path.join(BASE_DIR, 'config', 'profiles.json')

# Caminhos comuns para o executável do SPAdes em diferentes sistemas
COMMON_SPADES_PATHS = [
    "/usr/bin/spades.py",
    "/usr/local/bin/spades.py",
    "~/SPAdes/bin/spades.py",
    "~/spades/bin/spades.py",
    "/opt/spades/bin/spades.py",
    "/opt/SPAdes/bin/spades.py",
    "~/miniconda3/envs/spades/bin/spades.py",
    "~/anaconda3/envs/spades/bin/spades.py"
]

def ensure_dirs_exist():
    """Garante que os diretórios necessários existam"""
    for directory in [TEMP_DIR, RESULTS_DIR, LOGS_DIR]:
        os.makedirs(directory, exist_ok=True)