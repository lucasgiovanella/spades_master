#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import socket
import threading
import time
import re
from datetime import datetime
import tarfile
import paramiko
import scp
from utils.logging_utils import log_info, log_error, log_warning

class JobManager:
    """Classe para gerenciar trabalhos do SPAdes remotamente"""
    def __init__(self, status_updater, ssh_utils=None):
        self.status_updater = status_updater
        self.ssh = None
        self.scp_client = None
        self.connected = False
        self.job_running = False
        self.job_id = None
        self.connection_info = {}
        self.spades_path = None 
        self.job_pid = None
        self.job_output_file = None
        self.allocated_memory = 0  # Memória alocada em MB
        
    def connect(self, host, port, username, password=None, key_path=None, use_key=False):
        """
        Conecta ao servidor remoto
        
        Args:
            host: Endereço do servidor
            port: Porta SSH
            username: Nome de usuário
            password: Senha (se não usar chave)
            key_path: Caminho para a chave SSH
            use_key: True para usar autenticação por chave
            
        Returns:
            bool: True se conectado com sucesso
        """
        try:
            # Validar parâmetros
            if not host or not username:
                self.status_updater.update_log("Servidor ou usuário não fornecido", "ERROR")
                return False
                
            if use_key and (not key_path or not os.path.isfile(key_path)):
                self.status_updater.update_log("Arquivo de chave inválido ou não encontrado", "ERROR")
                return False
                
            if not use_key and not password:
                self.status_updater.update_log("Senha não fornecida para autenticação", "ERROR")
                return False
                
            # Sanitizar valores
            host = host.strip()
            # Remover qualquer ":porta" que possa ter sido acidentalmente incluído no hostname
            if ":" in host:
                host = host.split(":")[0]
                
            username = username.strip()
            port = int(port.strip()) if port and port.strip().isdigit() else 22
            
            # Verificar se a porta é padrão (22) ou não
            port_display = "" if port == 22 else f" (porta {port})"
            self.status_updater.update_status(f"Conectando a {username}@{host}{port_display}...")
            self.status_updater.update_log(f"Tentando conectar a {username}@{host}{port_display}")
            
            # Armazenar informações de conexão
            self.connection_info = {
                "host": host,
                "port": port,
                "username": username
            }
            
            # Limpar conexões anteriores
            if self.ssh is not None:
                self.ssh.close()
                
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Conectar com chave ou senha
            connect_kwargs = {
                "hostname": host,
                "port": port,
                "username": username,
                "timeout": 10
            }
            
            if use_key and key_path:
                try:
                    key = paramiko.RSAKey.from_private_key_file(key_path)
                    connect_kwargs["pkey"] = key
                except Exception as key_error:
                    self.status_updater.update_log(f"Erro ao carregar chave SSH: {str(key_error)}", "ERROR")
                    return False
            else:
                connect_kwargs["password"] = password
                
            # Tentar conectar
            self.ssh.connect(**connect_kwargs)
                
             # Verificar se o SPAdes está instalado
            # Primeiro tentar o comando which
            stdin, stdout, stderr = self.ssh.exec_command("which spades.py || echo 'NOT_FOUND'")
            spades_path = stdout.read().decode().strip()
            
            # Se não encontrar com which, verificar manualmente os locais comuns
            if spades_path == 'NOT_FOUND':
                from config.settings import COMMON_SPADES_PATHS
                
                for path in COMMON_SPADES_PATHS:
                    path = os.path.expanduser(path)  # Expandir '~' se presente
                    stdin, stdout, stderr = self.ssh.exec_command(f"[ -f {path} ] && [ -x {path} ] && echo '{path}' || echo 'NOT_FOUND'")
                    result = stdout.read().decode().strip()
                    if result != 'NOT_FOUND':
                        spades_path = result
                        break
            
            if spades_path == 'NOT_FOUND':
                self.status_updater.update_status("Erro: SPAdes não encontrado automaticamente")
                self.status_updater.update_log("SPAdes não encontrado automaticamente no servidor. Um diálogo será exibido para configuração manual.", "WARNING")
                return False
                
            # Armazenar o caminho do SPAdes para uso posterior
            self.spades_path = spades_path
            self.status_updater.update_log(f"SPAdes encontrado: {spades_path}", "SUCCESS")
            
            # Criar cliente SCP
            transport = self.ssh.get_transport()
            if transport is None:
                self.status_updater.update_log("Erro ao obter transporte SSH", "ERROR")
                self.ssh.close()
                return False
                
            self.scp_client = scp.SCPClient(transport, progress=self._progress_callback)
            
            self.connected = True
            self.status_updater.update_status("Conectado ao servidor")
            # Verificar se a porta é padrão (22) ou não
            port_info = f" (porta {port})" if port != 22 else ""
            self.status_updater.update_log(f"Conectado com sucesso a {username}@{host}{port_info}", "SUCCESS")
            return True
            
        except paramiko.AuthenticationException:
            self.status_updater.update_status("Erro de autenticação")
            self.status_updater.update_log("Falha na autenticação. Verifique usuário/senha ou chave SSH.", "ERROR")
            return False
        except paramiko.SSHException as e:
            self.status_updater.update_status(f"Erro SSH: {str(e)}")
            self.status_updater.update_log(f"Erro de conexão SSH: {str(e)}", "ERROR")
            return False
        except socket.timeout:
            self.status_updater.update_status("Tempo esgotado na conexão")
            self.status_updater.update_log("Tempo esgotado ao tentar conectar. Verifique o endereço e rede.", "ERROR")
            return False
        except socket.gaierror:
            self.status_updater.update_status("Erro de resolução de nome")
            self.status_updater.update_log("Não foi possível resolver o nome do servidor. Verifique o endereço.", "ERROR")
            return False
        except Exception as e:
            self.status_updater.update_status(f"Erro: {str(e)}")
            self.status_updater.update_log(f"Erro ao conectar: {str(e)}", "ERROR")
            return False
            
    def disconnect(self):
        """Desconecta do servidor"""
        if self.ssh:
            try:
                self.ssh.close()
            except Exception as e:
                self.status_updater.update_log(f"Erro ao desconectar SSH: {str(e)}", "WARNING")
                
        if self.scp_client:
            try:
                self.scp_client.close()
            except Exception as e:
                self.status_updater.update_log(f"Erro ao desconectar SCP: {str(e)}", "WARNING")
                
        self.connected = False
        self.status_updater.update_status("Desconectado do servidor")
        self.status_updater.update_log("Desconectado do servidor")
        
    def check_server_resources(self):
        """
        Verifica os recursos disponíveis no servidor
        
        Returns:
            dict: Dicionário com informações de CPU, memória e disco
        """
        if not self.connected or not self.ssh:
            return None
            
        try:
            # Verificar CPU
            stdin, stdout, stderr = self.ssh.exec_command("nproc 2>/dev/null || echo 'unknown'")
            cpu_output = stdout.read().decode().strip()
            cpu_count = int(cpu_output) if cpu_output.isdigit() else "Desconhecido"
            
            # Verificar RAM
            stdin, stdout, stderr = self.ssh.exec_command("free -m 2>/dev/null | grep Mem || echo 'unknown'")
            mem_output = stdout.read().decode().strip()
            
            if mem_output and mem_output != 'unknown':
                mem_info = mem_output.split()
                if len(mem_info) >= 4:
                    total_mem = int(mem_info[1])
                    used_mem = int(mem_info[2])
                    free_mem = int(mem_info[3])
                else:
                    total_mem = used_mem = free_mem = "Desconhecido"
            else:
                total_mem = used_mem = free_mem = "Desconhecido"
            
            # Verificar espaço em disco
            stdin, stdout, stderr = self.ssh.exec_command("df -h --output=avail / 2>/dev/null | tail -1 || echo 'unknown'")
            disk_avail = stdout.read().decode().strip()
            
            resources = {
                "cpu_count": cpu_count,
                "total_mem": total_mem,
                "used_mem": used_mem,
                "free_mem": free_mem,
                "disk_avail": disk_avail
            }
            
            return resources
            
        except Exception as e:
            self.status_updater.update_log(f"Erro ao verificar recursos: {str(e)}", "ERROR")
            return None
            
    def prepare_remote_dir(self, remote_dir):
        """
        Prepara o diretório remoto para receber os arquivos
        
        Args:
            remote_dir: Caminho do diretório remoto
            
        Returns:
            bool: True se preparado com sucesso
        """
        if not self.connected or not self.ssh:
            return False
            
        try:
            self.status_updater.update_status("Preparando diretório remoto...")
            
            # Sanitizar caminho remoto
            remote_dir = remote_dir.strip().rstrip('/')
            if not remote_dir:
                remote_dir = "/tmp/spades_jobs"
                self.status_updater.update_log(f"Usando diretório remoto padrão: {remote_dir}")
                
            # Verificar se o diretório já existe
            stdin, stdout, stderr = self.ssh.exec_command(f"[ -d {remote_dir} ] && echo 'EXISTS' || echo 'NOT_EXISTS'")
            dir_exists = stdout.read().decode().strip()
            
            if dir_exists == 'EXISTS':
                self.status_updater.update_log(f"Diretório remoto já existe: {remote_dir}")
            else:
                # Criar diretório
                stdin, stdout, stderr = self.ssh.exec_command(f"mkdir -p {remote_dir}")
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status == 0:
                    self.status_updater.update_log(f"Diretório remoto criado: {remote_dir}")
                else:
                    error = stderr.read().decode().strip()
                    self.status_updater.update_log(f"Erro ao criar diretório remoto: {error}", "ERROR")
                    return False
                    
            # Verificar permissões
            stdin, stdout, stderr = self.ssh.exec_command(f"touch {remote_dir}/.test_write && rm {remote_dir}/.test_write && echo 'OK' || echo 'ERROR'")
            write_test = stdout.read().decode().strip()
            
            if write_test != 'OK':
                self.status_updater.update_log(f"Aviso: Sem permissão de escrita no diretório remoto: {remote_dir}", "WARNING")
                
            return True
                
        except Exception as e:
            self.status_updater.update_log(f"Erro ao preparar diretório remoto: {str(e)}", "ERROR")
            return False
            
    def upload_files(self, local_files, remote_dir):
        """
        Envia arquivos para o servidor remoto
        
        Args:
            local_files: Lista de caminhos dos arquivos locais
            remote_dir: Caminho do diretório remoto
            
        Returns:
            bool: True se enviados com sucesso
        """
        if not self.connected or not self.scp_client:
            return False
            
        try:
            # Validar arquivos
            if not local_files or not all(os.path.exists(f) for f in local_files):
                self.status_updater.update_log("Arquivos locais inválidos ou não encontrados", "ERROR")
                return False
                
            # Verificar diretório remoto
            if not remote_dir:
                self.status_updater.update_log("Diretório remoto não especificado", "ERROR")
                return False
                
            self.status_updater.update_status("Enviando arquivos...")
            
            # Verificar espaço em disco
            total_size = sum(os.path.getsize(f) for f in local_files)
            total_size_mb = total_size / (1024 * 1024)
            
            self.status_updater.update_log(f"Tamanho total dos arquivos: {total_size_mb:.2f} MB")
            
            # Enviar arquivos
            for local_file in local_files:
                if not os.path.exists(local_file):
                    self.status_updater.update_log(f"Arquivo não encontrado: {local_file}", "ERROR")
                    continue
                    
                filename = os.path.basename(local_file)
                self.status_updater.update_log(f"Enviando arquivo: {filename}")
                
                # Verificar tamanho do arquivo
                file_size = os.path.getsize(local_file)
                file_size_mb = file_size / (1024 * 1024)
                self.status_updater.update_log(f"Tamanho do arquivo: {file_size_mb:.2f} MB")
                
                try:
                    self.scp_client.put(local_file, f"{remote_dir}/{filename}")
                    self.status_updater.update_log(f"Arquivo enviado: {filename}", "SUCCESS")
                except Exception as upload_error:
                    self.status_updater.update_log(f"Erro ao enviar arquivo {filename}: {str(upload_error)}", "ERROR")
                    return False
                
            return True
            
        except Exception as e:
            self.status_updater.update_log(f"Erro ao enviar arquivos: {str(e)}", "ERROR")
            return False
            
    def _parse_spades_progress(self, output):
        """
        Extrai informações de progresso do SPAdes a partir da saída do log
        
        Args:
            output: Texto do log do SPAdes
            
        Returns:
            str: Mensagem de progresso formatada ou None
        """
        try:
            # SPAdes não tem um formato padrão de progresso, então vamos buscar por padrões comuns
            stage_match = re.search(r'===\s*(.*?)\s*===', output)
            if stage_match:
                return f"Estágio: {stage_match.group(1)}"
                
            # Buscar por porcentagens
            percent_match = re.search(r'(\d+(?:\.\d+)?)%', output)
            if percent_match:
                return f"Progresso: {percent_match.group(1)}%"
                
            # Buscar por mensagens específicas
            if "Assembly" in output and "has started" in output:
                return "Iniciando montagem"
                
            if "K-mer counting" in output:
                return "Contando k-mers"
                
            if "Error correction" in output:
                return "Corrigindo erros"
                
            if "done" in output.lower() or "finished" in output.lower():
                return "Finalizando etapa atual"
                
            return None
        except Exception:
            return None
            
    def _progress_callback(self, filename, size, sent):
        """Callback para progresso do SCP"""
        try:
            if size:
                percent = float(sent) / float(size) * 100
                self.status_updater.update_progress(int(percent))
        except Exception:
            pass
            
    def run_spades(self, remote_dir, read1, read2, output_dir, threads, memory=None, mode="isolate", kmer=None, advanced_params=None):
        """
        Executa o SPAdes no servidor remoto
        
        Args:
            remote_dir: Diretório remoto
            read1: Caminho do arquivo de leitura 1
            read2: Caminho do arquivo de leitura 2
            output_dir: Diretório de saída
            threads: Número de threads
            memory: Memória máxima (opcional)
            mode: Modo de execução do SPAdes
            kmer: Tamanhos de k-mer (opcional)
            
        Returns:
            bool: True se iniciado com sucesso
        """
        if not self.connected or not self.ssh:
            return False
        
        try:
            # Validar parâmetros
            if not remote_dir or not read1 or not read2 or not output_dir or not threads:
                self.status_updater.update_log("Parâmetros incompletos para execução do SPAdes", "ERROR")
                return False
                
            remote_dir = remote_dir.strip()
            output_dir = output_dir.strip()
            
            if not output_dir:
                output_dir = "assembly"
                
            # Verificar se os arquivos existem no servidor
            read1_file = os.path.basename(read1)
            read2_file = os.path.basename(read2)
            
            stdin, stdout, stderr = self.ssh.exec_command(f"[ -f {remote_dir}/{read1_file} ] && [ -f {remote_dir}/{read2_file} ] && echo 'OK' || echo 'MISSING'")
            files_exist = stdout.read().decode().strip()
            
            if files_exist != 'OK':
                self.status_updater.update_log("Arquivos de leitura não encontrados no servidor. Envie-os primeiro.", "ERROR")
                return False
            
            # Usar o caminho completo do SPAdes
            spades_command = self.spades_path if self.spades_path else "spades.py"
                
            # Verificar se o SPAdes pode ser executado (teste simples)
            self.status_updater.update_log("Verificando se o SPAdes pode ser executado...")
            test_cmd = f"{spades_command} --version"
            stdin, stdout, stderr = self.ssh.exec_command(test_cmd)
            spades_version = stdout.read().decode().strip()
            spades_error = stderr.read().decode().strip()
            
            if not spades_version and spades_error:
                self.status_updater.update_log(f"Erro ao executar SPAdes: {spades_error}", "ERROR")
                return False
                
            self.status_updater.update_log(f"Versão do SPAdes: {spades_version}", "SUCCESS")
                
            self.status_updater.update_status("Iniciando SPAdes...")
            self.job_running = True
            
            # Sanitizar thread count
            if not str(threads).isdigit():
                threads = "4"
                self.status_updater.update_log("Número de threads inválido. Usando 4 threads.", "WARNING")
                
            # Sanitizar memory
            if memory and not str(memory).isdigit():
                memory = None
                self.status_updater.update_log("Valor de memória inválido. Usando padrão do SPAdes.", "WARNING")
                
            # Construir o comando SPAdes - SIMPLIFICADO E CORRIGIDO
            # Usar apenas uma mudança de diretório
            command = f"cd {remote_dir} && {spades_command}"
            command += f" -1 {read1_file} -2 {read2_file}"
            command += f" -t {threads}"
            
            if memory:
                command += f" -m {memory}"
                
            # Validar modo
            valid_modes = ["isolate", "careful", "meta", "rna", "plasmid", "metaviral", "metaplasmid", "bio", "corona"]
            if mode not in valid_modes:
                mode = "isolate"
                self.status_updater.update_log(f"Modo inválido. Usando modo '{mode}'.", "WARNING")
                
            # Tratar corretamente isolate e os outros modos
            if mode == "isolate":
                # O modo isolate é o padrão, não precisa de flag
                pass
            elif mode == "careful":
                command += " --careful"
            else:
                command += f" --{mode}"
                
            # Validar k-mer
            if kmer:
                # Verificar se é uma lista válida de k-mers (números separados por vírgula)
                kmer_valid = True
                kmer_list = kmer.split(',')
                for k in kmer_list:
                    if not k.strip().isdigit():
                        kmer_valid = False
                        break
                        
                if kmer_valid:
                    command += f" -k {kmer}"
                else:
                    self.status_updater.update_log("Valores de k-mer inválidos. Usando padrão do SPAdes.", "WARNING")
                
            command += f" -o {output_dir}"
            
            # Registrar o comando
            self.status_updater.update_log(f"Executando comando: {command}")
            
            # Iniciar o comando em background
            job_id = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Melhorar o redirecionamento para capturar todos os erros
            log_file = f"{remote_dir}/spades_{job_id}.log"
            error_file = f"{remote_dir}/spades_{job_id}.err"
            
            # Usando o formato de execução em background mais confiável
            # e capturando tanto stdout quanto stderr
            full_command = f"{command} > {log_file} 2> {error_file} & echo $!"
            
            self.status_updater.update_log(f"Executando: {full_command}")
            stdin, stdout, stderr = self.ssh.exec_command(full_command)
            
            # Obter PID do processo
            pid = stdout.read().decode().strip()
            
            # Verificar se obtivemos um PID válido
            if not pid or not pid.isdigit():
                self.status_updater.update_log("Falha ao iniciar o processo SPAdes", "ERROR")
                
                # Verificar se há mensagens de erro
                stdin, stdout, stderr = self.ssh.exec_command(f"cat {error_file} 2>/dev/null || echo 'Sem arquivo de erro'")
                error_output = stdout.read().decode().strip()
                if error_output and error_output != 'Sem arquivo de erro':
                    self.status_updater.update_log(f"Erro ao iniciar SPAdes: {error_output}", "ERROR")
                
                # Verificar se há alguma saída que possa ajudar a diagnosticar
                stdin, stdout, stderr = self.ssh.exec_command(f"[ -f {log_file} ] && cat {log_file} || echo 'Nenhum log disponível'")
                log_output = stdout.read().decode().strip()
                if log_output and log_output != 'Nenhum log disponível':
                    self.status_updater.update_log(f"Log do SPAdes: {log_output}", "INFO")
                
                # Tentar executar um teste mais simples para ver se o comando básico funciona
                stdin, stdout, stderr = self.ssh.exec_command(f"{spades_command} --help 2>/dev/null | head -5")
                help_output = stdout.read().decode().strip()
                if not help_output:
                    self.status_updater.update_log(f"O comando SPAdes não pode ser executado. Verifique o caminho: {spades_command}", "ERROR")
                    
                self.job_running = False
                return False
            
            self.job_id = pid
            
            # Verificar imediatamente se o processo está realmente em execução
            stdin, stdout, stderr = self.ssh.exec_command(f"ps -p {pid} -o pid,comm | grep -v PID || echo 'NOT_RUNNING'")
            process_check = stdout.read().decode().strip()
            
            if process_check == 'NOT_RUNNING':
                # Processo não está em execução, provavelmente falhou no início
                self.status_updater.update_log("O processo SPAdes não está em execução após o início. Verificando erros...", "ERROR")
                
                # Verificar log de erro
                stdin, stdout, stderr = self.ssh.exec_command(f"cat {error_file} 2>/dev/null || echo 'Sem mensagens de erro'")
                error_log = stdout.read().decode().strip()
                self.status_updater.update_log(f"Mensagens de erro: {error_log}", "ERROR")
                
                # Verificar se há alguma saída de log
                stdin, stdout, stderr = self.ssh.exec_command(f"[ -f {log_file} ] && cat {log_file} || echo 'Sem log disponível'")
                log_output = stdout.read().decode().strip()
                if log_output and log_output != 'Sem log disponível':
                    self.status_updater.update_log(f"Conteúdo do log: {log_output}", "INFO")
                
                # Verificar permissão no diretório
                stdin, stdout, stderr = self.ssh.exec_command(f"ls -ld {remote_dir}")
                dir_perms = stdout.read().decode().strip()
                self.status_updater.update_log(f"Permissões do diretório remoto: {dir_perms}", "INFO")
                
                self.job_running = False
                return False
            
            self.status_updater.update_log(f"SPAdes iniciado com PID: {pid}", "SUCCESS")
            self.status_updater.update_status(f"SPAdes executando (PID: {pid})")
            
            # Iniciar thread para monitorar o processo
            monitor_thread = threading.Thread(
                target=self._monitor_job,
                args=(remote_dir, pid, job_id, output_dir),
                daemon=True
            )
            monitor_thread.start()
            
            # Salvar a memória alocada
            self.allocated_memory = int(memory)
            
            # Modificar para salvar o comando em um arquivo temporário e executá-lo com controle de PID
            job_script = f"job_spades_{int(time.time())}.sh"
            job_output = f"spades_output_{int(time.time())}.log"
            self.job_output_file = f"{remote_dir}/{job_output}"
            
            # Criar script de execução
            script_content = f"""#!/bin/bash
{command} > {job_output} 2>&1 &
echo $!  # Retorna o PID do processo
"""
            
            stdin, stdout, stderr = self.ssh.exec_command(
                f"cd {remote_dir} && echo '{script_content}' > {job_script} && chmod +x {job_script} && ./{job_script}"
            )
            
            # Capturar o PID do processo
            self.job_pid = stdout.read().decode().strip()
            if self.job_pid and self.job_pid.isdigit():
                self.job_running = True
                return True, f"SPAdes iniciado com sucesso. PID: {self.job_pid}"
            else:
                self.job_running = False
                return False, "Falha ao iniciar o SPAdes."
            
            return True
                
        except Exception as e:
            self.job_running = False
            self.status_updater.update_log(f"Erro ao iniciar SPAdes: {str(e)}", "ERROR")
            self.status_updater.update_status("Erro ao iniciar SPAdes")
            return False
            
    def _monitor_job(self, remote_dir, pid, job_id, output_dir):
        """
        Monitora o progresso do job em execução
        
        Args:
            remote_dir: Diretório remoto
            pid: PID do processo
            job_id: ID do job
            output_dir: Diretório de saída
        """
        try:
            # Contador de tentativas sem resposta
            no_response_count = 0
            max_no_response = 5  # Número máximo de tentativas sem resposta
            
            # Verificar se o processo está rodando a cada 30 segundos
            while self.job_running and self.connected:
                try:
                    # Verificar se o processo ainda existe
                    stdin, stdout, stderr = self.ssh.exec_command(f"ps -p {pid} -o pid,pcpu,pmem,time,comm | tail -n 1")
                    process_info = stdout.read().decode().strip()
                    
                    if process_info:
                        # Processo ainda está rodando
                        self.status_updater.update_log(f"Status do processo: {process_info}")
                        no_response_count = 0  # Resetar contador
                        
                        # Verificar log do SPAdes
                        # Usar tail com o caminho completo para maior compatibilidade
                        log_cmd = f"/usr/bin/tail -n 20 {remote_dir}/spades_{job_id}.log 2>/dev/null || echo ''"
                        stdin, stdout, stderr = self.ssh.exec_command(log_cmd)
                        log_output = stdout.read().decode().strip()
                        
                        # Verificar também o arquivo de erro
                        err_cmd = f"/usr/bin/tail -n 20 {remote_dir}/spades_{job_id}.err 2>/dev/null || echo ''"
                        stdin, stdout, stderr = self.ssh.exec_command(err_cmd)
                        err_output = stdout.read().decode().strip()
                        
                        # Combinar outputs se ambos existirem
                        if log_output and err_output:
                            combined_output = f"=== Log de Saída ===\n{log_output}\n\n=== Log de Erro ===\n{err_output}"
                        elif log_output:
                            combined_output = log_output
                        elif err_output:
                            combined_output = f"=== Log de Erro ===\n{err_output}"
                        else:
                            combined_output = ""
                        
                        # Extrair informações de progresso, se disponíveis
                        if combined_output:
                            progress_info = self._parse_spades_progress(combined_output)
                            if progress_info:
                                self.status_updater.update_status(f"SPAdes executando - {progress_info}")
                            
                            # Registrar para depuração
                            self.status_updater.update_log("Conteúdo do log do SPAdes:", "INFO")
                            if len(combined_output) > 500:  # Se for muito grande, mostrar apenas parte
                                self.status_updater.update_log(combined_output[:500] + "...", "INFO")
                            else:
                                self.status_updater.update_log(combined_output, "INFO")
                                
                    else:
                        # Processo não encontrado ou terminado
                        no_response_count += 1
                        
                        if no_response_count >= max_no_response:
                            # Várias tentativas sem resposta, considerar processo terminado
                            self.status_updater.update_log("Processo SPAdes concluído", "SUCCESS")
                            self.status_updater.update_status("SPAdes concluído")
                            self.job_running = False
                            
                            # Verificar resultado
                            stdin, stdout, stderr = self.ssh.exec_command(f"ls -la {remote_dir}/{output_dir} 2>/dev/null || echo 'NOT_FOUND'")
                            output_files = stdout.read().decode().strip()
                            
                            if output_files != 'NOT_FOUND':
                                self.status_updater.update_log(f"Arquivos de saída:\n{output_files}")
                                
                                # Verificar se o arquivo de scaffolds foi gerado
                                stdin, stdout, stderr = self.ssh.exec_command(f"[ -f {remote_dir}/{output_dir}/scaffolds.fasta ] && echo 'OK' || echo 'NOT_FOUND'")
                                scaffolds_exists = stdout.read().decode().strip()
                                
                                if scaffolds_exists == 'OK':
                                    self.status_updater.update_log("Montagem concluída com sucesso! O arquivo scaffolds.fasta foi gerado.", "SUCCESS")
                                else:
                                    self.status_updater.update_log("Aviso: O arquivo scaffolds.fasta não foi encontrado. A montagem pode ter falhado.", "WARNING")
                            else:
                                self.status_updater.update_log(f"Diretório de saída não encontrado: {remote_dir}/{output_dir}", "ERROR")
                            
                            break
                            
                        self.status_updater.update_log(f"Processo {pid} não encontrado. Tentativa {no_response_count}/{max_no_response}.", "WARNING")
                        
                except Exception as e:
                    self.status_updater.update_log(f"Erro ao monitorar processo: {str(e)}", "ERROR")
                    no_response_count += 1
                    
                    if no_response_count >= max_no_response:
                        self.status_updater.update_log("Muitas falhas ao monitorar o processo. Considerando finalizado.", "WARNING")
                        self.job_running = False
                        break
                        
                time.sleep(30)
                
        except Exception as e:
            self.status_updater.update_log(f"Erro ao monitorar o job: {str(e)}", "ERROR")
            self.job_running = False
            
    def check_job_status(self):
        """
        Verifica o status do job atual
        
        Returns:
            bool: True se o job ainda está rodando
        """
        if not self.connected or not self.ssh or not self.job_id:
            return False
            
        try:
            stdin, stdout, stderr = self.ssh.exec_command(f"ps -p {self.job_id} -o pid= 2>/dev/null")
            output = stdout.read().decode().strip()
            
            if output:
                return True  # O job ainda está rodando
            else:
                return False  # O job terminou ou não foi encontrado
                
        except Exception:
            return False
            
    def cancel_job(self):
        """
        Cancela o job em execução
        
        Returns:
            bool: True se cancelado com sucesso
        """
        if not self.connected or not self.ssh:
            self.status_updater.update_log("Servidor não conectado para cancelar job", "WARNING")
            return False
            
        if not self.job_pid and not self.job_id:
            self.status_updater.update_log("Nenhum job em execução para cancelar", "WARNING")
            return False
            
        try:
            self.status_updater.update_status("Cancelando job...")
            
            # Usar o PID principal se disponível, caso contrário usar job_id
            pid_to_kill = self.job_pid if self.job_pid else self.job_id
            self.status_updater.update_log(f"Tentando cancelar processo com PID {pid_to_kill}", "WARNING")
            
            # Encontrar processos filhos do SPAdes (para garantir que tudo seja limpo)
            stdin, stdout, stderr = self.ssh.exec_command(f"pgrep -P {pid_to_kill} || echo ''")
            child_pids = stdout.read().decode().strip().split()
            
            # Tentar primeiro um SIGTERM para terminar o processo corretamente
            stdin, stdout, stderr = self.ssh.exec_command(f"kill {pid_to_kill}")
            exit_status = stdout.channel.recv_exit_status()
            
            # Matar também os processos filhos se houver
            if child_pids:
                child_pids_str = " ".join(child_pids)
                self.status_updater.update_log(f"Cancelando processos filhos: {child_pids_str}", "WARNING")
                stdin, stdout, stderr = self.ssh.exec_command(f"kill {child_pids_str}")
            
            # Verificar se o processo ainda está em execução
            time.sleep(1)  # Pequena pausa para o sistema operacional processar o sinal
            stdin, stdout, stderr = self.ssh.exec_command(f"ps -p {pid_to_kill} -o pid= 2>/dev/null || echo ''")
            still_running = stdout.read().decode().strip()
            
            if not still_running:
                self.status_updater.update_log(f"Job {pid_to_kill} cancelado", "SUCCESS")
                self.status_updater.update_status("Job cancelado")
                self.job_running = False
                return True
            else:
                # Se falhar, tenta SIGKILL (força o encerramento)
                stdin, stdout, stderr = self.ssh.exec_command(f"kill -9 {pid_to_kill}")
                
                # Matar processos filhos com SIGKILL também
                if child_pids:
                    stdin, stdout, stderr = self.ssh.exec_command(f"kill -9 {child_pids_str}")
                    
                # Verificar novamente
                time.sleep(1)
                stdin, stdout, stderr = self.ssh.exec_command(f"ps -p {pid_to_kill} -o pid= 2>/dev/null || echo ''")
                still_running = stdout.read().decode().strip()
                
                if not still_running:
                    self.status_updater.update_log(f"Job {pid_to_kill} forçado a terminar", "SUCCESS")
                    self.status_updater.update_status("Job forçado a terminar")
                    self.job_running = False
                    return True
                else:
                    error = stderr.read().decode().strip()
                    self.status_updater.update_log(f"Erro ao cancelar job: {error}", "ERROR")
                    return False
                
        except Exception as e:
            self.status_updater.update_log(f"Erro ao cancelar job: {str(e)}", "ERROR")
            return False
                
    def download_results(self, remote_dir, output_dir, local_dir):
        """
        Baixa os resultados do servidor
        
        Args:
            remote_dir: Diretório remoto
            output_dir: Diretório de saída no servidor
            local_dir: Diretório local para salvar os resultados
            
        Returns:
            bool: True se baixado com sucesso
        """
        if not self.connected or not self.scp_client:
            return False
            
        try:
            # Validar diretórios
            if not remote_dir or not output_dir or not local_dir:
                self.status_updater.update_log("Diretórios necessários não especificados", "ERROR")
                return False
                
            # Sanitizar caminhos
            remote_dir = remote_dir.strip()
            output_dir = output_dir.strip()
            local_dir = local_dir.strip()
            
            if not remote_dir or not output_dir:
                self.status_updater.update_log("Diretório remoto ou pasta de saída não especificados", "ERROR")
                return False
                
            self.status_updater.update_status("Verificando resultados...")
            
            # Verificar se o diretório remoto existe
            stdin, stdout, stderr = self.ssh.exec_command(f"[ -d {remote_dir}/{output_dir} ] && echo 'OK' || echo 'NOT_FOUND'")
            dir_exists = stdout.read().decode().strip()
            
            if dir_exists != 'OK':
                self.status_updater.update_log(f"Diretório remoto não encontrado: {remote_dir}/{output_dir}", "ERROR")
                return False
                
            # Verificar os arquivos principais
            main_files = ["scaffolds.fasta", "contigs.fasta", "assembly_graph.fastg", "spades.log"]
            found_files = []
            
            for file in main_files:
                stdin, stdout, stderr = self.ssh.exec_command(f"[ -f {remote_dir}/{output_dir}/{file} ] && echo 'OK' || echo 'NOT_FOUND'")
                file_exists = stdout.read().decode().strip()
                
                if file_exists == 'OK':
                    found_files.append(file)
                    
            if not found_files:
                self.status_updater.update_log("Nenhum arquivo principal de saída encontrado. A montagem pode ter falhado.", "ERROR")
                
                # Verificar se há algum arquivo de log que possa indicar o problema
                stdin, stdout, stderr = self.ssh.exec_command(f"find {remote_dir} -name '*.log' | head -1")
                log_file = stdout.read().decode().strip()
                
                if log_file:
                    self.status_updater.update_log(f"Encontrado arquivo de log: {log_file}")
                    stdin, stdout, stderr = self.ssh.exec_command(f"tail -n 20 {log_file}")
                    log_content = stdout.read().decode().strip()
                    self.status_updater.update_log(f"Últimas linhas do log:\n{log_content}")
                    
                return False
                
            # Criar diretório local se não existir
            try:
                os.makedirs(local_dir, exist_ok=True)
            except Exception as dir_error:
                self.status_updater.update_log(f"Erro ao criar diretório local: {str(dir_error)}", "ERROR")
                return False
                
            self.status_updater.update_status("Baixando resultados...")
            self.status_updater.update_log(f"Arquivos encontrados: {', '.join(found_files)}")
                
            # Comprimir resultados no servidor
            self.status_updater.update_log("Comprimindo resultados no servidor...")
            compress_cmd = f"cd {remote_dir} && tar -czf {output_dir}.tar.gz {output_dir}"
            stdin, stdout, stderr = self.ssh.exec_command(compress_cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error = stderr.read().decode().strip()
                self.status_updater.update_log(f"Erro ao comprimir resultados: {error}", "ERROR")
                
                # Tentar baixar arquivos individuais
                self.status_updater.update_log("Tentando baixar arquivos individuais...")
                
                try:
                    for file in found_files:
                        self.status_updater.update_log(f"Baixando {file}...")
                        local_file_dir = os.path.join(local_dir, output_dir)
                        os.makedirs(local_file_dir, exist_ok=True)
                        self.scp_client.get(f"{remote_dir}/{output_dir}/{file}", os.path.join(local_file_dir, file))
                        self.status_updater.update_log(f"Arquivo {file} baixado com sucesso", "SUCCESS")
                except Exception as e:
                    self.status_updater.update_log(f"Erro ao baixar arquivo: {str(e)}", "ERROR")
                    return False
                    
                return True
                
            # Baixar o arquivo comprimido
            local_tar_path = os.path.join(local_dir, f"{output_dir}.tar.gz")
            self.status_updater.update_log(f"Baixando arquivo comprimido para {local_tar_path}...")
            
            try:
                self.scp_client.get(f"{remote_dir}/{output_dir}.tar.gz", local_tar_path)
            except Exception as e:
                self.status_updater.update_log(f"Erro ao baixar arquivo comprimido: {str(e)}", "ERROR")
                return False
                
            # Descomprimir localmente
            self.status_updater.update_log("Descomprimindo arquivo localmente...")
            try:
                with tarfile.open(local_tar_path, "r:gz") as tar:
                    tar.extractall(path=local_dir)
                    
                # Remover arquivo tar
                os.remove(local_tar_path)
                
                self.status_updater.update_log(f"Resultados baixados com sucesso para {local_dir}/{output_dir}", "SUCCESS")
                self.status_updater.update_status("Resultados baixados com sucesso")
                return True
            except Exception as extract_error:
                self.status_updater.update_log(f"Erro ao descomprimir arquivo: {str(extract_error)}", "ERROR")
                return False
                
        except Exception as e:
            self.status_updater.update_log(f"Erro ao baixar resultados: {str(e)}", "ERROR")
            self.status_updater.update_status("Erro ao baixar resultados")
            return False
