# Logging utilities 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Utilitários para logging da aplicação
"""

import logging
import sys

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Criar logger
logger = logging.getLogger('spades')

def log_info(message):
    """Log mensagem de informação"""
    logger.info(message)

def log_error(message):
    """Log mensagem de erro"""
    logger.error(message)

def log_warning(message):
    """Log mensagem de aviso"""
    logger.warning(message)

def log_success(message):
    """Log mensagem de sucesso"""
    logger.info(f"SUCCESS: {message}")