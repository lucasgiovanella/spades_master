# Execution endpoints 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API para execução e monitoramento de jobs SPAdes
"""

import os
import threading
import time
from flask import Blueprint, request, jsonify, current_app
from flask_socketio import emit
from werkzeug.utils import secure_filename
from backend.models.server_profile import ServerProfile
from backend.services.job_manager import JobManager
from backend.utils.socket_updater import SocketUpdater
from backend.utils.logging_utils import log_info, log_error, log_warning
from backend.app import socketio

# Criar blueprint
bp = Blueprint('execution', __name__, url_prefix='/api/execution')

# Instâncias das classes necessárias
profiles_manager = ServerProfile()
socket_updater = SocketUpdater(namespace='/logs')
job_manager = JobManager(socket_updater)

# Diretório temporário para armazenar arquivos enviados
UPLOAD_FOLDER = 'temp'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Iniciar o socket updater
socket_updater.start()

@bp.route('/connect', methods=['POST'])
def connect_to_server():
    """Conecta ao servidor escolhido"""
    try:
        data = request.json
        
        # Validar data
        if not data or 'profile_name' not in data:
            return jsonify({
                'status': 'error',
                'message': "Nome do perfil não informado"
            }), 400
            
        profile_name = data['profile_name']
        
        # Obter perfil do servidor
        profile = profiles_manager.get_profile(profile_name)
        if not profile:
            return jsonify({
                'status': 'error',
                'message': f"Perfil '{profile_name}' não encontrado"
            }), 404
            
        # Desconectar se já estiver conectado
        if job_manager.connected:
            job_manager.disconnect()
            
        # Conectar em thread separada para não bloquear
        socket_updater.update_status(f"Conectando a {profile['username']}@{profile['host']}...")
        
        # Thread para conexão
        def do_connect():
            success = job_manager.connect(
                profile['host'],
                profile['port'],
                profile['username'],
                profile['password'] if not profile['use_key'] else '',
                profile['key_path'] if profile['use_key'] else '',
                profile['use_key']
            )
            
            if success:
                # Verificar recursos do servidor
                resources = job_manager.check_server_resources()
                
                # Enviar atualização
                socketio.emit('connect_result', {
                    'success': True,
                    'message': f"Conectado com sucesso a {profile['username']}@{profile['host']}",
                    'resources': resources,
                    'spades_path': job_manager.spades_path
                }, namespace='/logs')
                
                # Verificar se SPAdes está disponível
                if job_manager.spades_path:
                    socket_updater.update_log(f"SPAdes encontrado: {job_manager.spades_path}", "SUCCESS")
                else:
                    socket_updater.update_log("SPAdes não encontrado automaticamente no servidor", "WARNING")
                    
            else:
                # Falha na conexão
                socketio.emit('connect_result', {
                    'success': False,
                    'message': "Falha ao conectar com o servidor"
                }, namespace='/logs')
        
        # Iniciar thread
        connect_thread = threading.Thread(target=do_connect)
        connect_thread.daemon = True
        connect_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': "Conexão iniciada. Aguarde o resultado via WebSocket."
        })
    except Exception as e:
        log_error(f"Erro ao conectar: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao conectar: {str(e)}"
        }), 500

@bp.route('/disconnect', methods=['POST'])
def disconnect_from_server():
    """Desconecta do servidor atual"""
    try:
        if job_manager.connected:
            job_manager.disconnect()
            socket_updater.update_log("Desconectado do servidor", "INFO")
            return jsonify({
                'status': 'success',
                'message': "Desconectado do servidor com sucesso"
            })
        else:
            return jsonify({
                'status': 'warning',
                'message': "Não há conexão ativa para desconectar"
            })
    except Exception as e:
        log_error(f"Erro ao desconectar: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao desconectar: {str(e)}"
        }), 500

@bp.route('/resources', methods=['GET'])
def check_resources():
    """Verifica os recursos disponíveis no servidor"""
    try:
        if not job_manager.connected:
            return jsonify({
                'status': 'error',
                'message': "Não há conexão ativa com o servidor"
            }), 400
            
        # Verificar recursos
        resources = job_manager.check_server_resources()
        
        if resources:
            socket_updater.update_log("Informações de recursos obtidas com sucesso", "SUCCESS")
            return jsonify({
                'status': 'success',
                'resources': resources
            })
        else:
            return jsonify({
                'status': 'error',
                'message': "Não foi possível obter informações de recursos"
            }), 500
    except Exception as e:
        log_error(f"Erro ao verificar recursos: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao verificar recursos: {str(e)}"
        }), 500

@bp.route('/upload', methods=['POST'])
def upload_files():
    """Recebe arquivos enviados pelo usuário"""
    try:
        if 'reads' not in request.files:
            return jsonify({
                'status': 'error',
                'message': "Nenhum arquivo enviado"
            }), 400
            
        files = request.files.getlist('reads')
        
        # Verificar se há arquivos
        if not files or all(file.filename == '' for file in files):
            return jsonify({
                'status': 'error',
                'message': "Nenhum arquivo selecionado"
            }), 400
            
        # Salvar arquivos
        file_paths = []
        for file in files:
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                file_paths.append({
                    'name': filename,
                    'path': file_path,
                    'size': os.path.getsize(file_path)
                })
                
        socket_updater.update_log(f"{len(file_paths)} arquivo(s) recebido(s) com sucesso", "SUCCESS")
        
        return jsonify({
            'status': 'success',
            'message': f"{len(file_paths)} arquivo(s) recebido(s) com sucesso",
            'files': file_paths
        })
    except Exception as e:
        log_error(f"Erro ao receber arquivos: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao receber arquivos: {str(e)}"
        }), 500

@bp.route('/prepare', methods=['POST'])
def prepare_and_upload():
    """Prepara o diretório remoto e envia os arquivos"""
    try:
        data = request.json
        
        # Validar data
        if not data:
            return jsonify({
                'status': 'error',
                'message': "Dados não informados"
            }), 400
            
        # Verificar se há conexão ativa
        if not job_manager.connected:
            return jsonify({
                'status': 'error',
                'message': "Não há conexão ativa com o servidor"
            }), 400
            
        # Obter parâmetros
        remote_dir = data.get('remote_dir', '/tmp/spades_jobs')
        file_paths = data.get('file_paths', [])
        
        # Verificar se há arquivos para enviar
        if not file_paths:
            return jsonify({
                'status': 'error',
                'message': "Nenhum arquivo para enviar"
            }), 400
            
        # Thread para preparação e upload
        def do_prepare_and_upload():
            # Preparar diretório remoto
            if not job_manager.prepare_remote_dir(remote_dir):
                socketio.emit('prepare_result', {
                    'success': False,
                    'message': "Falha ao preparar diretório remoto"
                }, namespace='/logs')
                return
                
            # Enviar arquivos
            socket_updater.update_log(f"Enviando {len(file_paths)} arquivo(s) para {remote_dir}...", "INFO")
            success = job_manager.upload_files(file_paths, remote_dir)
            
            if success:
                socketio.emit('prepare_result', {
                    'success': True,
                    'message': "Arquivos enviados com sucesso",
                    'remote_dir': remote_dir,
                    'files': [os.path.basename(path) for path in file_paths]
                }, namespace='/logs')
            else:
                socketio.emit('prepare_result', {
                    'success': False,
                    'message': "Falha ao enviar arquivos"
                }, namespace='/logs')
        
        # Iniciar thread
        upload_thread = threading.Thread(target=do_prepare_and_upload)
        upload_thread.daemon = True
        upload_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': "Preparação e envio iniciados. Aguarde o resultado via WebSocket."
        })
    except Exception as e:
        log_error(f"Erro na preparação: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro na preparação: {str(e)}"
        }), 500

@bp.route('/run', methods=['POST'])
def run_spades():
    """Inicia a execução do SPAdes no servidor"""
    try:
        data = request.json
        
        # Validar data
        if not data:
            return jsonify({
                'status': 'error',
                'message': "Dados não informados"
            }), 400
            
        # Verificar se há conexão ativa
        if not job_manager.connected:
            return jsonify({
                'status': 'error',
                'message': "Não há conexão ativa com o servidor"
            }), 400
            
        # Verificar se job já está rodando
        if job_manager.job_running:
            return jsonify({
                'status': 'error',
                'message': "Já existe um job em execução"
            }), 400
            
        # Obter parâmetros
        remote_dir = data.get('remote_dir', '/tmp/spades_jobs')
        read1 = data.get('read1')
        read2 = data.get('read2')
        output_dir = data.get('output_dir', 'assembly')
        threads = data.get('threads', '8')
        memory = data.get('memory', '')
        mode = data.get('mode', 'isolate')
        kmer = data.get('kmer', '')
        
        # Validar parâmetros obrigatórios
        if not read1 or not read2:
            return jsonify({
                'status': 'error',
                'message': "Arquivos de leitura (R1 e R2) são obrigatórios"
            }), 400
            
        # Thread para execução do SPAdes
        def do_run_spades():
            socket_updater.update_log(f"Iniciando SPAdes em {remote_dir}...", "INFO")
            
            # Verificar SPAdes
            if not job_manager.spades_path:
                socket_updater.update_log("SPAdes não encontrado no servidor. Verifique a instalação.", "ERROR")
                socketio.emit('run_result', {
                    'success': False,
                    'message': "SPAdes não encontrado no servidor"
                }, namespace='/logs')
                return
                
            # Construir comando de preview para o log
            spades_command = job_manager.spades_path
            cmd_preview = f"{spades_command} -1 {os.path.basename(read1)} -2 {os.path.basename(read2)} -t {threads} --{mode} -o {output_dir}"
            socket_updater.update_log(f"Comando a ser executado: {cmd_preview}", "INFO")
            
            # Executar SPAdes
            success = job_manager.run_spades(
                remote_dir,
                read1,
                read2,
                output_dir,
                threads,
                memory,
                mode,
                kmer
            )
            
            if success:
                socketio.emit('run_result', {
                    'success': True,
                    'message': "SPAdes iniciado com sucesso",
                    'job_id': job_manager.job_id,
                    'job_pid': job_manager.job_pid,
                    'job_output_file': job_manager.job_output_file
                }, namespace='/logs')
                
                # Inicia o monitoramento em outra thread
                monitoring_thread = threading.Thread(target=do_monitoring)
                monitoring_thread.daemon = True
                monitoring_thread.start()
            else:
                socketio.emit('run_result', {
                    'success': False,
                    'message': "Falha ao iniciar SPAdes"
                }, namespace='/logs')
        
        # Thread para monitoramento contínuo
        def do_monitoring():
            start_time = time.time()
            while job_manager.job_running and job_manager.connected:
                try:
                    # Verificar se o processo ainda existe
                    process_info = job_manager.get_user_processes()
                    
                    if process_info and process_info.get('spades_processes'):
                        # Calcular tempo decorrido
                        elapsed = time.time() - start_time
                        hours, remainder = divmod(int(elapsed), 3600)
                        minutes, seconds = divmod(remainder, 60)
                        elapsed_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                        
                        # Pegar informações de CPU e memória
                        cpu_usage = process_info.get('spades_cpu', 0)
                        mem_usage = process_info.get('spades_mem', 0)
                        mem_mb = process_info.get('spades_mem_mb', 0)
                        
                        # Enviar atualização
                        socketio.emit('monitoring_update', {
                            'status': 'running',
                            'elapsed_time': elapsed_str,
                            'cpu_usage': cpu_usage,
                            'memory_usage': mem_usage,
                            'memory_mb': mem_mb,
                            'processes': len(process_info.get('spades_processes', []))
                        }, namespace='/logs')
                        
                        # Verificar log para atualização de fase
                        if job_manager.job_output_file:
                            try:
                                stdin, stdout, stderr = job_manager.ssh.exec_command(
                                    f"grep -E '(===|Stage)' {job_manager.job_output_file} | tail -n 1"
                                )
                                phase = stdout.read().decode().strip()
                                if phase:
                                    socketio.emit('phase_update', {
                                        'phase': phase
                                    }, namespace='/logs')
                            except Exception:
                                pass
                    else:
                        # Processo não encontrado, verificar se job terminou
                        socketio.emit('monitoring_update', {
                            'status': 'checking'
                        }, namespace='/logs')
                        
                        # Verificar se o job realmente terminou
                        if not job_manager.check_job_status():
                            job_manager.job_running = False
                            socket_updater.update_log("Job SPAdes concluído", "SUCCESS")
                            socketio.emit('job_completed', {
                                'success': True,
                                'message': "Job SPAdes concluído com sucesso",
                                'remote_dir': remote_dir,
                                'output_dir': output_dir
                            }, namespace='/logs')
                            break
                except Exception as e:
                    socket_updater.update_log(f"Erro durante monitoramento: {str(e)}", "ERROR")
                
                # Aguardar antes da próxima verificação
                time.sleep(3)
                
            # Se saiu do loop porque a conexão foi perdida
            if not job_manager.connected and job_manager.job_running:
                socket_updater.update_log("Monitoramento interrompido: conexão perdida", "WARNING")
                socketio.emit('monitoring_update', {
                    'status': 'disconnected',
                    'message': "Conexão com o servidor perdida"
                }, namespace='/logs')
        
        # Iniciar thread de execução
        run_thread = threading.Thread(target=do_run_spades)
        run_thread.daemon = True
        run_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': "Execução do SPAdes iniciada. Acompanhe o progresso via WebSocket."
        })
    except Exception as e:
        log_error(f"Erro ao iniciar SPAdes: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao iniciar SPAdes: {str(e)}"
        }), 500

@bp.route('/cancel', methods=['POST'])
def cancel_job():
    """Cancela o job em execução"""
    try:
        # Verificar se há conexão ativa
        if not job_manager.connected:
            return jsonify({
                'status': 'error',
                'message': "Não há conexão ativa com o servidor"
            }), 400
            
        # Verificar se há job em execução
        if not job_manager.job_running:
            return jsonify({
                'status': 'error',
                'message': "Não há job em execução para cancelar"
            }), 400
            
        # Thread para cancelar o job
        def do_cancel_job():
            socket_updater.update_log("Cancelando job...", "WARNING")
            success = job_manager.cancel_job()
            
            if success:
                socketio.emit('cancel_result', {
                    'success': True,
                    'message': "Job cancelado com sucesso"
                }, namespace='/logs')
            else:
                socketio.emit('cancel_result', {
                    'success': False,
                    'message': "Falha ao cancelar job"
                }, namespace='/logs')
        
        # Iniciar thread
        cancel_thread = threading.Thread(target=do_cancel_job)
        cancel_thread.daemon = True
        cancel_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': "Cancelamento do job iniciado. Aguarde o resultado via WebSocket."
        })
    except Exception as e:
        log_error(f"Erro ao cancelar job: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao cancelar job: {str(e)}"
        }), 500

@bp.route('/status', methods=['GET'])
def get_job_status():
    """Obtém o status atual do job"""
    try:
        # Verificar se há conexão ativa
        if not job_manager.connected:
            return jsonify({
                'status': 'error',
                'message': "Não há conexão ativa com o servidor"
            }), 400
            
        # Verificar status do job
        job_running = job_manager.job_running
        job_id = job_manager.job_id
        job_pid = job_manager.job_pid
        
        # Obter processos do usuário
        processes_info = job_manager.get_user_processes()
        
        return jsonify({
            'status': 'success',
            'job_running': job_running,
            'job_id': job_id,
            'job_pid': job_pid,
            'processes_info': processes_info
        })
    except Exception as e:
        log_error(f"Erro ao obter status do job: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao obter status do job: {str(e)}"
        }), 500

# Configurar eventos do Socket.IO
@socketio.on('connect', namespace='/logs')
def socket_connect():
    """Evento de conexão do Socket.IO"""
    emit('connected', {'message': 'Conectado ao servidor de logs'})

@socketio.on('disconnect', namespace='/logs')
def socket_disconnect():
    """Evento de desconexão do Socket.IO"""
    pass