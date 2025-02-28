#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os
from datetime import datetime
import warnings
from config.settings import LOG_DIR, APP_NAME

# Suprimir avisos de depreciação
warnings.filterwarnings("ignore", message=".*TripleDES has been moved.*")
warnings.filterwarnings("ignore", message=".*other_params is deprecated.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

try:
    from cryptography.utils import CryptographyDeprecationWarning
    warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)
except ImportError:
    pass

def setup_logger():
    """Configura e retorna o logger principal da aplicação"""
    # Garantir que o diretório de logs existe
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Nome do arquivo de log com timestamp
    log_file = os.path.join(LOG_DIR, f"{APP_NAME.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Configurar logger
    logger = logging.getLogger(APP_NAME)
    logger.setLevel(logging.INFO)
    
    # Configurar formato
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Handler para arquivo
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Handler para console (opcional)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Logger global
logger = setup_logger()

def log_info(message):
    """Log de informação"""
    logger.info(message)

def log_warning(message):
    """Log de aviso"""
    logger.warning(message)

def log_error(message):
    """Log de erro"""
    logger.error(message)

def log_success(message):
    """Log de sucesso (usando INFO)"""
    logger.info(f"[SUCCESS] {message}")