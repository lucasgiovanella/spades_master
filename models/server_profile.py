#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from datetime import datetime
from config.settings import PROFILES_FILE
from utils.logging_utils import log_info, log_error, log_warning

class ServerProfile:
    """Classe para gerenciar perfis de servidores"""
    def __init__(self):
        self.profile_file = PROFILES_FILE
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(self.profile_file), exist_ok=True)
        
        # Carregar perfis
        self.profiles = self._load_profiles()
    
    def _load_profiles(self):
        """Carrega os perfis do arquivo JSON"""
        try:
            if os.path.exists(self.profile_file):
                with open(self.profile_file, 'r', encoding='utf-8') as f:
                    log_info(f"Carregando perfis de {self.profile_file}")
                    content = f.read().strip()
                    if not content:
                        log_warning("Arquivo de perfis está vazio")
                        return {}
                    return json.loads(content)
            log_info("Arquivo de perfis não encontrado. Criando novo.")
            return {}
        except json.JSONDecodeError as e:
            log_error(f"Erro ao decodificar arquivo de perfis: {str(e)}")
            # Fazer backup do arquivo corrompido
            if os.path.exists(self.profile_file):
                backup_file = f"{self.profile_file}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
                try:
                    os.rename(self.profile_file, backup_file)
                    log_info(f"Backup do arquivo corrompido criado: {backup_file}")
                except Exception as be:
                    log_error(f"Erro ao criar backup: {str(be)}")
            return {}
        except Exception as e:
            log_error(f"Erro ao carregar perfis: {str(e)}")
            return {}
    
    def _save_profiles(self):
        """Salva os perfis em arquivo JSON"""
        try:
            # Garantir que o diretório exista
            os.makedirs(os.path.dirname(self.profile_file), exist_ok=True)
            
            # Validar os dados antes de salvar
            if not isinstance(self.profiles, dict):
                log_error(f"Dados de perfis inválidos: {type(self.profiles)}")
                return False
                
            with open(self.profile_file, 'w', encoding='utf-8') as f:
                json.dump(self.profiles, f, indent=2, ensure_ascii=False)
            log_info(f"Perfis salvos em {self.profile_file}")
            return True
        except Exception as e:
            log_error(f"Erro ao salvar perfis: {str(e)}")
            return False
            
    def get_profile_names(self):
        """Retorna uma lista com os nomes dos perfis cadastrados"""
        return list(self.profiles.keys())
        
    def get_profile(self, name):
        """Retorna um perfil específico pelo nome"""
        return self.profiles.get(name, {})
        
    def add_profile(self, name, host, port, username, password, key_path, use_key):
        """Adiciona ou atualiza um perfil no sistema"""
        # Verificações de validação
        if not self._validate_profile_data(name, host, username, password, key_path, use_key):
            return False
            
        # Sanitizar valores
        name = name.strip()
        host = host.strip()
        port = port.strip() if port else "22"
        username = username.strip()
        
        # Garantir que a porta seja um número
        if not port.isdigit():
            port = "22"
        
        # Armazenar perfil
        self.profiles[name] = {
            "host": host,
            "port": port,
            "username": username,
            "password": password if not use_key else "",
            "key_path": key_path if use_key else "",
            "use_key": use_key
        }
        
        result = self._save_profiles()
        if result:
            log_info(f"Perfil '{name}' adicionado com sucesso")
        return result
    
    def _validate_profile_data(self, name, host, username, password, key_path, use_key):
        """Valida os dados de um perfil antes de salvar"""
        if not name or not host or not username:
            log_warning("Tentativa de adicionar perfil com campos obrigatórios vazios")
            return False
            
        # Verificar método de autenticação
        if use_key:
            if not key_path or not os.path.isfile(key_path):
                log_warning(f"Arquivo de chave não encontrado: {key_path}")
                return False
        else:
            if not password:
                log_warning("Senha não fornecida para autenticação por senha")
                return False
                
        return True
        
    def update_profile(self, name, host, port, username, password, key_path, use_key):
        """Atualiza um perfil existente"""
        if name in self.profiles:
            log_info(f"Atualizando perfil '{name}'")
            return self.add_profile(name, host, port, username, password, key_path, use_key)
        log_warning(f"Tentativa de atualizar perfil inexistente: '{name}'")
        return False
        
    def delete_profile(self, name):
        """Remove um perfil"""
        if name in self.profiles:
            del self.profiles[name]
            log_info(f"Perfil '{name}' excluído")
            return self._save_profiles()
        log_warning(f"Tentativa de excluir perfil inexistente: '{name}'")
        return False