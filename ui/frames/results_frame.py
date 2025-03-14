#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
import os
import re
from ui.styles import ResponsiveUI

class ResultsFrame(ttk.Frame):
    """Frame para visualizar e gerenciar resultados"""
    def __init__(self, parent, config_frame, job_manager, status_updater, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.parent = parent
        self.config_frame = config_frame
        self.job_manager = job_manager
        self.status_updater = status_updater
        
        # Criar interface
        self._create_widgets()
        
    def _create_widgets(self):
        """Cria os widgets do frame de resultados"""
        # Obter a instância de ResponsiveUI do aplicativo principal
        self.responsive_ui = self.parent.master.responsive_ui if hasattr(self.parent, 'master') and hasattr(self.parent.master, 'responsive_ui') else None
        
        # Definir padding responsivo
        padding = self.responsive_ui.get_padding() if self.responsive_ui else 10
        
        # Botões para operações de resultados
        button_frame = ttk.Frame(self, style='Card.TFrame')
        button_frame.pack(fill=tk.X, padx=padding, pady=padding//2)
        
        # Opções de download
        download_frame = ttk.LabelFrame(button_frame, text="Opções de Download", style='Card.TFrame')
        download_frame.grid(row=0, column=0, padx=padding//2, pady=padding//2, sticky=tk.W)
        
        # Botão para baixar apenas arquivos importantes
        ttk.Button(
            download_frame, 
            text="Baixar Arquivos Importantes", 
            command=lambda: self._download_results(important_only=True)
        ).grid(row=0, column=0, padx=5, pady=5)
        
        # Botão para baixar todos os arquivos
        ttk.Button(
            download_frame, 
            text="Baixar Todos os Arquivos", 
            command=lambda: self._download_results(important_only=False)
        ).grid(row=0, column=1, padx=5, pady=5)
        
        # Frame para outros botões
        other_frame = ttk.Frame(button_frame, style='Card.TFrame')
        other_frame.grid(row=0, column=1, padx=padding//2, pady=padding//2)
        
        # Botão para abrir pasta de resultados
        ttk.Button(
            other_frame, 
            text="Abrir Pasta de Resultados", 
            command=self._open_results_folder,
            style="Primary.TButton"
        ).grid(row=0, column=0, padx=padding//2, pady=padding//2)
        
        # Botão para limpar arquivos remotos
        self.clean_button = ttk.Button(
            other_frame, 
            text="Limpar Arquivos Remotos", 
            command=self._clean_remote_files,
            style="Warning.TButton"  # Estilo para alertar o usuário
        )
        self.clean_button.grid(row=0, column=1, padx=5, pady=5)
        
        # Lista de arquivos de resultados
        results_frame = ttk.LabelFrame(self, text="Arquivos de Resultados", style='Card.TFrame')
        results_frame.pack(fill=tk.BOTH, expand=True, padx=padding, pady=padding//2)
        
        # Lista de arquivos
        self.results_text = tk.Text(results_frame, height=15, width=80, state='disabled')
        self.results_text.pack(fill=tk.BOTH, expand=True, padx=padding//2, pady=padding//2)
        
        # Informações sobre os resultados
        info_frame = ttk.LabelFrame(self, text="Informações da Montagem", style='Card.TFrame')
        info_frame.pack(fill=tk.BOTH, expand=True, padx=padding, pady=padding//2)
        
        # Sumário de resultados
        self.results_info_text = tk.Text(info_frame, height=8, width=80, state='disabled')
        self.results_info_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Tentar configurar estilo de botão de alerta (vermelho ou laranja)
        try:
            style = ttk.Style()
            style.configure("Warning.TButton", foreground="red", font=('Helvetica', 9, 'bold'))
            style.configure("Primary.TButton", foreground="black", font=('Helvetica', 9, 'bold'))
        except Exception:
            pass
        
    def _download_results(self, important_only=True):
        """
        Baixa os resultados do servidor
        
        Args:
            important_only: Se True, baixa apenas arquivos importantes
        """
        # Disparar evento para a classe principal com informação do tipo de download
        self.event_generate("<<DownloadResults>>", data={"important_only": important_only})
        
    def _open_results_folder(self):
        """Abre o diretório de resultados no explorador de arquivos"""
        # Disparar evento para a classe principal
        self.event_generate("<<OpenResultsFolder>>")
        
    def _clean_remote_files(self):
        """Solicita a limpeza dos arquivos remotos no servidor"""
        # Disparar evento para a classe principal
        self.event_generate("<<CleanRemoteFiles>>")
        
    def update_results_list(self, local_dir, output_dir):
        """
        Atualiza a lista de arquivos baixados
        
        Args:
            local_dir: Diretório local onde os resultados foram salvos
            output_dir: Nome da pasta de saída
        """
        local_output_path = os.path.join(local_dir, output_dir)
        
        if not os.path.exists(local_output_path):
            self.status_updater.update_log(f"Diretório de resultados não encontrado: {local_output_path}", "WARNING")
            return
            
        # Listar arquivos baixados
        results_text = self.results_text
        results_text.config(state='normal')
        results_text.delete(1.0, tk.END)
        
        # Verificar se foi um download seletivo
        is_selective = os.path.exists(os.path.join(local_output_path, "IMPORTANT_FILES_ONLY.txt"))
        if is_selective:
            results_text.insert(tk.END, "*** DOWNLOAD SELETIVO - Apenas arquivos essenciais foram baixados ***\n\n")
        
        # Obter lista de arquivos
        try:
            files = []
            for root, dirs, filenames in os.walk(local_output_path):
                for filename in filenames:
                    if filename == "IMPORTANT_FILES_ONLY.txt":
                        continue  # Pular o arquivo de marcação
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, local_output_path)
                    size = os.path.getsize(file_path)
                    files.append((rel_path, size))
                    
            # Mostrar principais arquivos primeiro
            main_files = ["scaffolds.fasta", "contigs.fasta", "assembly_graph.fastg", "spades.log"]
            
            results_text.insert(tk.END, "=== Arquivos Principais ===\n")
            for main_file in main_files:
                for file_path, size in files:
                    if file_path == main_file:
                        size_str = self._format_size(size)
                        results_text.insert(tk.END, f"{file_path} ({size_str})\n")
                        
            results_text.insert(tk.END, "\n=== Todos os Arquivos ===\n")
            for file_path, size in sorted(files):
                size_str = self._format_size(size)
                results_text.insert(tk.END, f"{file_path} ({size_str})\n")
                
            # Atualizar informações da montagem
            self._update_assembly_info(local_output_path)
                
        except Exception as e:
            results_text.insert(tk.END, f"Erro ao listar arquivos: {str(e)}")
            
        results_text.config(state='disabled')
        
    def _format_size(self, size_bytes):
        """
        Formata tamanho de arquivo para exibição
        
        Args:
            size_bytes: Tamanho do arquivo em bytes
            
        Returns:
            str: Tamanho formatado com unidade
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
        
    def _update_assembly_info(self, results_path):
        """
        Extrai e exibe informações sobre a montagem
        
        Args:
            results_path: Caminho para o diretório de resultados
        """
        # Extrair informações básicas da montagem
        info_text = self.results_info_text
        info_text.config(state='normal')
        info_text.delete(1.0, tk.END)
        
        try:
            # Tentar ler arquivo de log
            log_path = os.path.join(results_path, "spades.log")
            
            if os.path.exists(log_path):
                with open(log_path, 'r') as f:
                    log_content = f.read()
                    
                # Extrair informações relevantes
                info_text.insert(tk.END, "Informações da Montagem:\n\n")
                
                # Tentar extrair parâmetros usados
                params_match = re.search(r'Command line: (.*)', log_content)
                if params_match:
                    info_text.insert(tk.END, f"Parâmetros: {params_match.group(1)}\n\n")
                    
                # Tentar extrair estatísticas
                stats_found = False
                for line in log_content.split('\n'):
                    if ("contig" in line.lower() and "length" in line.lower() and 
                            any(x in line for x in [">=", "N50", "max"])):
                        info_text.insert(tk.END, line + "\n")
                        stats_found = True
                        
                if not stats_found:
                    # Tentar ler scaffolds.fasta
                    scaffolds_path = os.path.join(results_path, "scaffolds.fasta")
                    
                    if os.path.exists(scaffolds_path):
                        # Contar contigs e calcular comprimento total
                        contig_count = 0
                        total_length = 0
                        lengths = []
                        
                        with open(scaffolds_path, 'r') as f:
                            current_contig = ""
                            for line in f:
                                line = line.strip()
                                if line.startswith('>'):
                                    if current_contig:
                                        contig_length = len(current_contig)
                                        total_length += contig_length
                                        lengths.append(contig_length)
                                        current_contig = ""
                                    contig_count += 1
                                else:
                                    current_contig += line
                                    
                            # Adicionar último contig
                            if current_contig:
                                contig_length = len(current_contig)
                                total_length += contig_length
                                lengths.append(contig_length)
                                
                        # Calcular N50
                        if lengths:
                            lengths.sort(reverse=True)
                            cum_length = 0
                            n50 = 0
                            for length in lengths:
                                cum_length += length
                                if cum_length >= total_length / 2:
                                    n50 = length
                                    break
                                    
                            info_text.insert(tk.END, f"Contigs: {contig_count}\n")
                            info_text.insert(tk.END, f"Comprimento total: {total_length} bp\n")
                            info_text.insert(tk.END, f"Contig mais longo: {lengths[0]} bp\n")
                            info_text.insert(tk.END, f"N50: {n50} bp\n")
            else:
                info_text.insert(tk.END, "Arquivo de log não encontrado. A montagem pode não ter sido concluída.")
                
        except Exception as e:
            info_text.insert(tk.END, f"Erro ao analisar informações da montagem: {str(e)}")
            
        info_text.config(state='disabled')