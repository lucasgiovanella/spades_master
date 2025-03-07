# Results endpoints 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
API para gestão de resultados de montagens SPAdes
"""

import os
import shutil
import threading
import tempfile
import json
import re
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from werkzeug.utils import secure_filename
from backend.models.server_profile import ServerProfile
from backend.services.job_manager import JobManager
from backend.utils.socket_updater import SocketUpdater
from backend.utils.logging_utils import log_info, log_error, log_warning
from backend.app import socketio

# Criar blueprint
bp = Blueprint('results', __name__, url_prefix='/api/results')

# Instâncias das classes necessárias
profiles_manager = ServerProfile()
socket_updater = SocketUpdater(namespace='/logs')
job_manager = JobManager(socket_updater)

# Diretório para armazenar resultados
RESULTS_DIR = os.path.join(os.getcwd(), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)

@bp.route('/download', methods=['POST'])
def download_results():
    """Baixa os resultados do servidor"""
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
        output_dir = data.get('output_dir', 'assembly')
        important_only = data.get('important_only', True)
        
        # Validar parâmetros obrigatórios
        if not remote_dir or not output_dir:
            return jsonify({
                'status': 'error',
                'message': "Diretório remoto e diretório de saída são obrigatórios"
            }), 400
            
        # Verificar se o job está rodando
        if job_manager.job_running:
            socket_updater.update_log("Aviso: O job ainda está em execução. Baixando resultados parciais.", "WARNING")
            
        # Local para salvar
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_dir = os.path.join(RESULTS_DIR, f"{output_dir}_{timestamp}")
        os.makedirs(local_dir, exist_ok=True)
            
        # Thread para download dos resultados
        def do_download_results():
            socket_updater.update_log(f"Iniciando download de {'arquivos importantes' if important_only else 'todos os arquivos'}...", "INFO")
            success = job_manager.download_results(remote_dir, output_dir, local_dir, important_only)
            
            if success:
                # Obter lista de arquivos baixados
                files = []
                for root, dirs, filenames in os.walk(local_dir):
                    for filename in filenames:
                        file_path = os.path.join(root, filename)
                        rel_path = os.path.relpath(file_path, local_dir)
                        size = os.path.getsize(file_path)
                        files.append({
                            'name': rel_path,
                            'size': size,
                            'path': os.path.join(output_dir, rel_path)
                        })
                
                # Criar arquivo de metadados
                metadata = {
                    'timestamp': timestamp,
                    'remote_dir': remote_dir,
                    'output_dir': output_dir,
                    'important_only': important_only,
                    'download_date': datetime.now().isoformat(),
                    'file_count': len(files)
                }
                
                with open(os.path.join(local_dir, 'metadata.json'), 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Analisar arquivos para extrair estatísticas
                assembly_stats = analyze_assembly_results(local_dir)
                
                socketio.emit('download_result', {
                    'success': True,
                    'message': "Download concluído com sucesso",
                    'local_dir': local_dir,
                    'files': files,
                    'stats': assembly_stats
                }, namespace='/logs')
            else:
                socketio.emit('download_result', {
                    'success': False,
                    'message': "Falha ao baixar arquivos"
                }, namespace='/logs')
        
        # Iniciar thread
        download_thread = threading.Thread(target=do_download_results)
        download_thread.daemon = True
        download_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': "Download iniciado. Aguarde o resultado via WebSocket.",
            'local_dir': local_dir
        })
    except Exception as e:
        log_error(f"Erro ao baixar resultados: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao baixar resultados: {str(e)}"
        }), 500

@bp.route('/list', methods=['GET'])
def list_results():
    """Lista os resultados disponíveis localmente"""
    try:
        results = []
        for item in os.listdir(RESULTS_DIR):
            item_path = os.path.join(RESULTS_DIR, item)
            if os.path.isdir(item_path):
                # Verificar se há metadata
                metadata_path = os.path.join(item_path, 'metadata.json')
                metadata = {}
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                
                # Verificar se há scaffolds.fasta
                has_scaffolds = os.path.exists(os.path.join(item_path, 'scaffolds.fasta'))
                
                # Obter estatísticas básicas
                stats = analyze_assembly_results(item_path)
                
                results.append({
                    'name': item,
                    'path': item_path,
                    'date': metadata.get('download_date', ''),
                    'has_scaffolds': has_scaffolds,
                    'file_count': metadata.get('file_count', 0),
                    'stats': stats
                })
        
        return jsonify({
            'status': 'success',
            'results': results
        })
    except Exception as e:
        log_error(f"Erro ao listar resultados: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao listar resultados: {str(e)}"
        }), 500

@bp.route('/files/<path:result_path>', methods=['GET'])
def list_result_files(result_path):
    """Lista os arquivos de um resultado específico"""
    try:
        # Validar caminho
        full_path = os.path.join(RESULTS_DIR, result_path)
        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            return jsonify({
                'status': 'error',
                'message': f"Diretório não encontrado: {result_path}"
            }), 404
        
        # Obter lista de arquivos
        files = []
        for root, dirs, filenames in os.walk(full_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                rel_path = os.path.relpath(file_path, full_path)
                size = os.path.getsize(file_path)
                files.append({
                    'name': rel_path,
                    'size': size,
                    'path': os.path.join(result_path, rel_path)
                })
        
        return jsonify({
            'status': 'success',
            'result_path': result_path,
            'files': files
        })
    except Exception as e:
        log_error(f"Erro ao listar arquivos: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao listar arquivos: {str(e)}"
        }), 500

@bp.route('/file/<path:file_path>', methods=['GET'])
def get_result_file(file_path):
    """Baixa um arquivo específico de resultado"""
    try:
        # Validar caminho
        full_path = os.path.join(RESULTS_DIR, file_path)
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return jsonify({
                'status': 'error',
                'message': f"Arquivo não encontrado: {file_path}"
            }), 404
        
        # Enviar arquivo
        return send_file(full_path, as_attachment=True)
    except Exception as e:
        log_error(f"Erro ao obter arquivo: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao obter arquivo: {str(e)}"
        }), 500

@bp.route('/analyze/<path:result_path>', methods=['GET'])
def analyze_result(result_path):
    """Analisa os resultados de uma montagem"""
    try:
        # Validar caminho
        full_path = os.path.join(RESULTS_DIR, result_path)
        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            return jsonify({
                'status': 'error',
                'message': f"Diretório não encontrado: {result_path}"
            }), 404
        
        # Analisar resultados
        stats = analyze_assembly_results(full_path)
        
        return jsonify({
            'status': 'success',
            'result_path': result_path,
            'stats': stats
        })
    except Exception as e:
        log_error(f"Erro ao analisar resultados: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao analisar resultados: {str(e)}"
        }), 500

@bp.route('/clean', methods=['POST'])
def clean_remote_files():
    """Limpa os arquivos remotos no servidor"""
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
            
        # Verificar se job está rodando
        if job_manager.job_running:
            return jsonify({
                'status': 'error',
                'message': "Não é possível limpar arquivos enquanto um job está em execução"
            }), 400
            
        # Obter parâmetros
        remote_dir = data.get('remote_dir', '/tmp/spades_jobs')
        output_dir = data.get('output_dir')
        confirm = data.get('confirm', True)
        
        # Thread para limpeza dos arquivos
        def do_clean_remote_files():
            socket_updater.update_log(f"Iniciando limpeza de arquivos remotos em {remote_dir}...", "WARNING")
            success, message = job_manager.clean_remote_files(remote_dir, output_dir, confirm)
            
            if success:
                socketio.emit('clean_result', {
                    'success': True,
                    'message': message
                }, namespace='/logs')
            else:
                socketio.emit('clean_result', {
                    'success': False,
                    'message': message
                }, namespace='/logs')
        
        # Iniciar thread
        clean_thread = threading.Thread(target=do_clean_remote_files)
        clean_thread.daemon = True
        clean_thread.start()
        
        return jsonify({
            'status': 'success',
            'message': "Limpeza de arquivos iniciada. Aguarde o resultado via WebSocket."
        })
    except Exception as e:
        log_error(f"Erro ao limpar arquivos: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao limpar arquivos: {str(e)}"
        }), 500

@bp.route('/delete/<path:result_path>', methods=['DELETE'])
def delete_result(result_path):
    """Remove um resultado local"""
    try:
        # Validar caminho
        full_path = os.path.join(RESULTS_DIR, result_path)
        if not os.path.exists(full_path) or not os.path.isdir(full_path):
            return jsonify({
                'status': 'error',
                'message': f"Diretório não encontrado: {result_path}"
            }), 404
        
        # Remover diretório
        shutil.rmtree(full_path)
        
        return jsonify({
            'status': 'success',
            'message': f"Resultado '{result_path}' removido com sucesso"
        })
    except Exception as e:
        log_error(f"Erro ao remover resultado: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f"Erro ao remover resultado: {str(e)}"
        }), 500

def analyze_assembly_results(results_path):
    """
    Extrai estatísticas de montagem a partir dos arquivos de resultado
    
    Args:
        results_path: Caminho para o diretório de resultados
        
    Returns:
        dict: Dicionário com estatísticas da montagem
    """
    stats = {
        'has_scaffolds': False,
        'has_contigs': False,
        'scaffold_count': 0,
        'contig_count': 0,
        'total_length': 0,
        'n50': 0,
        'longest_scaffold': 0,
        'gc_content': 0,
        'command_line': '',
        'spades_version': ''
    }
    
    try:
        # Verificar arquivo de scaffolds
        scaffolds_path = os.path.join(results_path, 'scaffolds.fasta')
        if os.path.exists(scaffolds_path):
            stats['has_scaffolds'] = True
            
            # Analisar arquivo FASTA
            lengths = []
            total_length = 0
            gc_count = 0
            base_count = 0
            scaffold_count = 0
            
            with open(scaffolds_path, 'r') as f:
                current_seq = ""
                for line in f:
                    line = line.strip()
                    if line.startswith('>'):
                        if current_seq:
                            # Processar sequência anterior
                            seq_len = len(current_seq)
                            lengths.append(seq_len)
                            total_length += seq_len
                            
                            # Contar GC
                            gc_count += current_seq.count('G') + current_seq.count('C')
                            base_count += seq_len
                            
                            current_seq = ""
                        scaffold_count += 1
                    else:
                        current_seq += line
                
                # Processar última sequência
                if current_seq:
                    seq_len = len(current_seq)
                    lengths.append(seq_len)
                    total_length += seq_len
                    
                    # Contar GC
                    gc_count += current_seq.count('G') + current_seq.count('C')
                    base_count += seq_len
            
            # Calcular estatísticas
            stats['scaffold_count'] = scaffold_count
            stats['total_length'] = total_length
            
            if lengths:
                lengths.sort(reverse=True)
                stats['longest_scaffold'] = lengths[0]
                
                # Calcular N50
                cumulative = 0
                n50 = 0
                for length in lengths:
                    cumulative += length
                    if cumulative >= total_length / 2:
                        n50 = length
                        break
                
                stats['n50'] = n50
            
            # Calcular %GC
            if base_count > 0:
                stats['gc_content'] = round(gc_count / base_count * 100, 2)
        
        # Verificar arquivo de contigs
        contigs_path = os.path.join(results_path, 'contigs.fasta')
        if os.path.exists(contigs_path):
            stats['has_contigs'] = True
            
            # Contar contigs
            contig_count = 0
            with open(contigs_path, 'r') as f:
                for line in f:
                    if line.startswith('>'):
                        contig_count += 1
            
            stats['contig_count'] = contig_count
        
        # Verificar arquivo de log
        log_path = os.path.join(results_path, 'spades.log')
        if os.path.exists(log_path):
            with open(log_path, 'r') as f:
                log_content = f.read()
                
                # Extrair linha de comando
                cmd_match = re.search(r'Command line: (.*)', log_content)
                if cmd_match:
                    stats['command_line'] = cmd_match.group(1)
                
                # Extrair versão do SPAdes
                version_match = re.search(r'SPAdes version: (.*)', log_content)
                if version_match:
                    stats['spades_version'] = version_match.group(1)
    except Exception as e:
        log_error(f"Erro ao analisar resultados: {str(e)}")
    
    return stats