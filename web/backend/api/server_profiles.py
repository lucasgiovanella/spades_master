# Server profiles endpoints 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API para gerenciamento de perfis de servidor
"""

from flask import Blueprint, request, jsonify
from backend.models.server_profile import ServerProfile
from backend.utils.logging_utils import log_info, log_error, log_warning

# Criar blueprint
bp = Blueprint('profiles', __name__, url_prefix='/api/profiles')

# Instanciar a classe de perfis
profiles_manager = ServerProfile()

@bp.route('/', methods=['GET'])
def get_profiles():
    """Obtém a lista de todos os perfis disponíveis"""
    try:
        profile_names = profiles_manager.get_profile_names()
        return jsonify({
            'status': 'success',
            'profiles': profile_names
        })
    except Exception as e:
        log_error(f"Erro ao obter perfis: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao obter perfis: {str(e)}"
        }), 500

@bp.route('/<name>', methods=['GET'])
def get_profile(name):
    """Obtém os detalhes de um perfil específico"""
    try:
        profile = profiles_manager.get_profile(name)
        if not profile:
            return jsonify({
                'status': 'error',
                'message': f"Perfil '{name}' não encontrado"
            }), 404
            
        # Remover senha para segurança na resposta API
        if 'password' in profile:
            profile = profile.copy()  # Copiar para não modificar o original
            profile['password'] = '********' if profile['password'] else ''
            
        return jsonify({
            'status': 'success',
            'profile': profile
        })
    except Exception as e:
        log_error(f"Erro ao obter perfil '{name}': {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao obter perfil: {str(e)}"
        }), 500

@bp.route('/', methods=['POST'])
def add_profile():
    """Adiciona um novo perfil de servidor"""
    try:
        data = request.json
        
        # Validar dados obrigatórios
        required_fields = ['name', 'host', 'username']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'status': 'error',
                    'message': f"Campo obrigatório '{field}' não informado"
                }), 400
                
        # Verificar método de autenticação
        use_key = data.get('use_key', False)
        if use_key and (not data.get('key_path')):
            return jsonify({
                'status': 'error',
                'message': "Caminho da chave SSH não informado para autenticação por chave"
            }), 400
        elif not use_key and (not data.get('password')):
            return jsonify({
                'status': 'error',
                'message': "Senha não informada para autenticação por senha"
            }), 400
            
        # Adicionar perfil
        success = profiles_manager.add_profile(
            data['name'],
            data['host'],
            data.get('port', ''),  # Port is optional, defaults to empty string
            data['username'],
            data.get('password', ''),
            data.get('key_path', ''),
            use_key
        )
        
        if success:
            log_info(f"Perfil '{data['name']}' adicionado com sucesso")
            return jsonify({
                'status': 'success',
                'message': f"Perfil '{data['name']}' adicionado com sucesso"
            })
        else:
            log_warning(f"Não foi possível adicionar o perfil '{data['name']}'")
            return jsonify({
                'status': 'error',
                'message': "Não foi possível adicionar o perfil"
            }), 500
    except Exception as e:
        log_error(f"Erro ao adicionar perfil: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao adicionar perfil: {str(e)}"
        }), 500

@bp.route('/<name>', methods=['PUT'])
def update_profile(name):
    """Atualiza um perfil existente"""
    try:
        data = request.json
        
        # Verificar se o perfil existe
        if name not in profiles_manager.get_profile_names():
            return jsonify({
                'status': 'error',
                'message': f"Perfil '{name}' não encontrado"
            }), 404
            
        # Validar dados obrigatórios
        required_fields = ['host', 'username']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'status': 'error',
                    'message': f"Campo obrigatório '{field}' não informado"
                }), 400
                
        # Verificar método de autenticação
        use_key = data.get('use_key', False)
        if use_key and (not data.get('key_path')):
            return jsonify({
                'status': 'error',
                'message': "Caminho da chave SSH não informado para autenticação por chave"
            }), 400
        elif not use_key and (not data.get('password')):
            return jsonify({
                'status': 'error',
                'message': "Senha não informada para autenticação por senha"
            }), 400
            
        # Atualizar perfil
        success = profiles_manager.update_profile(
            name,
            data['host'],
            data.get('port', ''),  # Port is optional, defaults to empty string
            data['username'],
            data.get('password', ''),
            data.get('key_path', ''),
            use_key
        )
        
        if success:
            log_info(f"Perfil '{name}' atualizado com sucesso")
            return jsonify({
                'status': 'success',
                'message': f"Perfil '{name}' atualizado com sucesso"
            })
        else:
            log_warning(f"Não foi possível atualizar o perfil '{name}'")
            return jsonify({
                'status': 'error',
                'message': "Não foi possível atualizar o perfil"
            }), 500
    except Exception as e:
        log_error(f"Erro ao atualizar perfil '{name}': {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao atualizar perfil: {str(e)}"
        }), 500

@bp.route('/<name>', methods=['DELETE'])
def delete_profile(name):
    """Remove um perfil"""
    try:
        # Verificar se o perfil existe
        if name not in profiles_manager.get_profile_names():
            return jsonify({
                'status': 'error',
                'message': f"Perfil '{name}' não encontrado"
            }), 404
            
        # Remover perfil
        success = profiles_manager.delete_profile(name)
        
        if success:
            log_info(f"Perfil '{name}' removido com sucesso")
            return jsonify({
                'status': 'success',
                'message': f"Perfil '{name}' removido com sucesso"
            })
        else:
            log_warning(f"Não foi possível remover o perfil '{name}'")
            return jsonify({
                'status': 'error',
                'message': "Não foi possível remover o perfil"
            }), 500
    except Exception as e:
        log_error(f"Erro ao remover perfil '{name}': {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao remover perfil: {str(e)}"
        }), 500

@bp.route('/<name>/test', methods=['POST'])
def test_connection(name):
    """Testa a conexão com um servidor"""
    try:
        # Verificar se o perfil existe
        profile = profiles_manager.get_profile(name)
        if not profile:
            return jsonify({
                'status': 'error',
                'message': f"Perfil '{name}' não encontrado"
            }), 404
            
        # Importar JobManager para testar conexão
        from backend.services.job_manager import JobManager
        from backend.utils.socket_updater import SocketUpdater
        
        # Criar socket updater para atualização em tempo real
        socket_updater = SocketUpdater(namespace='/logs')
        
        # Criar instância temporária do JobManager
        job_manager = JobManager(socket_updater)
        
        # Tentar conectar
        host = profile['host']
        port = profile['port']
        username = profile['username']
        password = profile['password'] if not profile['use_key'] else ''
        key_path = profile['key_path'] if profile['use_key'] else ''
        use_key = profile['use_key']
        
        # Conectar de forma não-bloqueante
        socket_updater.update_status(f"Testando conexão com {username}@{host}...")
        
        # Usar um objeto de resposta para comunicação entre threads
        response = {
            'success': False,
            'message': '',
            'server_info': None
        }
        
        def do_test_connection():
            try:
                success = job_manager.connect(host, port, username, password, key_path, use_key)
                
                if success:
                    # Verificar recursos do servidor
                    resources = job_manager.check_server_resources()
                    response['server_info'] = resources
                    response['success'] = True
                    response['message'] = "Conexão estabelecida com sucesso!"
                    
                    # Verificar SPAdes
                    if job_manager.spades_path:
                        response['message'] += f" SPAdes encontrado: {job_manager.spades_path}"
                    else:
                        response['message'] += " SPAdes não encontrado automaticamente."
                        
                    # Desconectar após o teste
                    job_manager.disconnect()
                else:
                    response['success'] = False
                    response['message'] = "Falha ao conectar com o servidor. Verifique as credenciais."
            except Exception as e:
                response['success'] = False
                response['message'] = f"Erro ao testar conexão: {str(e)}"
        
        # Executar teste de conexão em uma thread para não bloquear
        import threading
        test_thread = threading.Thread(target=do_test_connection)
        test_thread.daemon = True
        test_thread.start()
        test_thread.join(timeout=10)  # Esperar no máximo 10 segundos
        
        # Verificar resposta
        if test_thread.is_alive():
            # O teste ainda está em execução após o timeout
            return jsonify({
                'status': 'error',
                'message': "Tempo esgotado ao tentar conectar com o servidor"
            }), 408
        
        # Retornar resultado
        if response['success']:
            return jsonify({
                'status': 'success',
                'message': response['message'],
                'server_info': response['server_info']
            })
        else:
            return jsonify({
                'status': 'error',
                'message': response['message']
            }), 500
    except Exception as e:
        log_error(f"Erro ao testar conexão com perfil '{name}': {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao testar conexão: {str(e)}"
        }), 500