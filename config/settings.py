#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
from pathlib import Path

# Versão do aplicativo
APP_VERSION = "1.2.1"
APP_NAME = "SPAdes Master"

# Caminhos comuns do SPAdes
COMMON_SPADES_PATHS = [
    "spades.py",  # no PATH do sistema
    "/usr/local/spades/bin/spades.py",
    "/usr/local/bin/spades.py",
    "/usr/bin/spades.py",
    "/opt/spades/bin/spades.py",
    "~/spades/bin/spades.py"
]

# Diretórios de configuração
def get_config_dir():
    """Retorna o diretório de configuração apropriado para o sistema operacional"""
    if platform.system() == "Windows":
        return os.path.join(os.environ["APPDATA"], APP_NAME)
    elif platform.system() == "Darwin":  # macOS
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    else:  # Linux/Unix
        return os.path.join(os.path.expanduser("~"), ".config", APP_NAME)

# Caminho para o arquivo de perfis
PROFILES_FILE = os.path.join(get_config_dir(), "server_profiles.json")

# Caminho para o diretório de logs
LOG_DIR = os.path.join(get_config_dir(), "logs")

# Criar diretórios se não existirem
def ensure_dirs_exist():
    """Garante que os diretórios necessários existam"""
    os.makedirs(get_config_dir(), exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)

# Modos de operação do SPAdes
SPADES_MODES = [
    "isolate", 
    "careful", 
    "meta", 
    "rna", 
    "plasmid", 
    "metaviral", 
    "metaplasmid", 
    "bio", 
    "corona"
]

# Valores padrão
DEFAULT_PORT = "22"
DEFAULT_THREADS = "8"
DEFAULT_MODE = "isolate"
DEFAULT_REMOTE_DIR = "/tmp/spades_jobs"
DEFAULT_OUTPUT_DIR = "assembly"