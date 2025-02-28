#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk
from config.settings import SPADES_MODES

class SPAdesParamsDialog:
    """Diálogo para configurações avançadas do SPAdes"""
    def __init__(self, parent, config_frame):
        self.parent = parent
        self.config_frame = config_frame
        
        # Criar janela
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Parâmetros Avançados do SPAdes")
        self.dialog.geometry("700x500")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centralizar no pai
        self.dialog.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.dialog.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.dialog.winfo_height()) // 2
        self.dialog.geometry(f"+{x}+{y}")
        
        # Copiar variáveis do config_frame
        self.threads = tk.StringVar(value=self.config_frame.threads.get())
        self.memory = tk.StringVar(value=self.config_frame.memory.get())
        self.mode = tk.StringVar(value=self.config_frame.mode.get())
        self.kmer = tk.StringVar(value=self.config_frame.kmer.get())
        
        # Variáveis adicionais para opções avançadas
        self.cov_cutoff = tk.StringVar(value="auto")
        self.phred_offset = tk.StringVar(value="auto")
        self.only_error_correction = tk.BooleanVar(value=False)
        self.only_assembler = tk.BooleanVar(value=False)
        self.careful = tk.BooleanVar(value=self.mode.get() == "careful")
        
        # Criar notebook para organizar os parâmetros
        self._create_notebook()
        
        # Botões de ação
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="OK", command=self._save_params).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Cancelar", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        
    def _create_notebook(self):
        """Cria o notebook para organizar os parâmetros"""
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Abas
        basic_tab = ttk.Frame(notebook, padding=10)
        advanced_tab = ttk.Frame(notebook, padding=10)
        help_tab = ttk.Frame(notebook, padding=10)
        
        notebook.add(basic_tab, text="Básico")
        notebook.add(advanced_tab, text="Avançado")
        notebook.add(help_tab, text="Ajuda")
        
        # Preencher aba básica
        self._setup_basic_tab(basic_tab)
        
        # Preencher aba avançada
        self._setup_advanced_tab(advanced_tab)
        
        # Preencher aba de ajuda
        self._setup_help_tab(help_tab)
        
    def _setup_basic_tab(self, parent):
        """Configura a aba de parâmetros básicos"""
        # Parâmetros básicos
        ttk.Label(parent, text="Modo de montagem:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        mode_combo = ttk.Combobox(parent, textvariable=self.mode, state="readonly", width=15, values=SPADES_MODES)
        mode_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(parent, text="Modo recomendado para o tipo de amostra").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(parent, text="Threads:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        threads_entry = ttk.Entry(parent, textvariable=self.threads, width=10)
        threads_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(parent, text="Número de threads para processamento paralelo").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(parent, text="Memória (GB):").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        mem_entry = ttk.Entry(parent, textvariable=self.memory, width=10)
        mem_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(parent, text="Limite de memória RAM em gigabytes").grid(row=2, column=2, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(parent, text="K-mers:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        kmer_entry = ttk.Entry(parent, textvariable=self.kmer, width=15)
        kmer_entry.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(parent, text="Lista de k-mers separados por vírgula (ex: 21,33,55)").grid(row=3, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Opção careful
        ttk.Checkbutton(
            parent, 
            text="Modo Careful", 
            variable=self.careful,
            command=self._toggle_careful
        ).grid(row=4, column=0, columnspan=3, sticky=tk.W, padx=5, pady=10)
        
        # Informações
        info_frame = ttk.LabelFrame(parent, text="Informação", padding=10)
        info_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=10)
        
        info_text = """
O SPAdes utiliza diferentes modos de montagem dependendo do tipo de amostra:

- isolate: para genomas isolados (modo padrão)
- careful: reduz o número de erros de montagem (mais lento)
- meta: para amostras metagenômicas
- rna: para montagem de transcriptomas
- plasmid: para montagem de plasmídeos
- corona: otimizado para montagem de coronavírus

Recomendação de memória: 1.5x o tamanho do genoma em GB
        """
        
        info_label = ttk.Label(info_frame, text=info_text, justify=tk.LEFT, wraplength=600)
        info_label.pack(fill=tk.X)
    
    def _setup_advanced_tab(self, parent):
        """Configura a aba de parâmetros avançados"""
        # Parâmetros avançados
        advanced_frame = ttk.Frame(parent)
        advanced_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Cutoff de cobertura
        ttk.Label(advanced_frame, text="Cutoff de cobertura:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=10)
        cov_frame = ttk.Frame(advanced_frame)
        cov_frame.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Radiobutton(
            cov_frame, 
            text="Auto", 
            variable=self.cov_cutoff, 
            value="auto"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            cov_frame, 
            text="Desativado", 
            variable=self.cov_cutoff, 
            value="off"
        ).pack(side=tk.LEFT, padx=5)
        
        custom_radio = ttk.Radiobutton(
            cov_frame, 
            text="Personalizado:", 
            variable=self.cov_cutoff, 
            value="custom"
        )
        custom_radio.pack(side=tk.LEFT, padx=5)
        
        self.custom_cov_entry = ttk.Entry(cov_frame, width=10)
        self.custom_cov_entry.pack(side=tk.LEFT, padx=5)
        
        # Offset de qualidade Phred
        ttk.Label(advanced_frame, text="Offset de qualidade Phred:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=10)
        phred_frame = ttk.Frame(advanced_frame)
        phred_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        ttk.Radiobutton(
            phred_frame, 
            text="Auto", 
            variable=self.phred_offset, 
            value="auto"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            phred_frame, 
            text="33", 
            variable=self.phred_offset, 
            value="33"
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(
            phred_frame, 
            text="64", 
            variable=self.phred_offset, 
            value="64"
        ).pack(side=tk.LEFT, padx=5)
        
        # Opções de pipeline
        pipeline_frame = ttk.LabelFrame(advanced_frame, text="Opções de Pipeline")
        pipeline_frame.grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)
        
        ttk.Checkbutton(
            pipeline_frame, 
            text="Apenas correção de erros (não realizar montagem)", 
            variable=self.only_error_correction
        ).pack(anchor=tk.W, padx=5, pady=5)
        
        ttk.Checkbutton(
            pipeline_frame, 
            text="Apenas montagem (pular correção de erros)", 
            variable=self.only_assembler
        ).pack(anchor=tk.W, padx=5, pady=5)
        
        # Informações adicionais
        info_frame = ttk.LabelFrame(advanced_frame, text="Informações")
        info_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, padx=5, pady=10)
        
        info_text = """
Parâmetros avançados:

- Cutoff de cobertura: controla a filtragem de contigs de baixa cobertura
  (auto: determinado automaticamente, off: desativado)
  
- Offset de qualidade Phred: formato da qualidade nos arquivos FASTQ
  (33 ou 64, dependendo da plataforma de sequenciamento)
  
- Apenas correção de erros: útil se você só precisar de leituras corrigidas
  
- Apenas montagem: útil se as leituras já estiverem corrigidas

Nota: As opções "Apenas correção de erros" e "Apenas montagem" são mutuamente exclusivas.
        """
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, wraplength=550).pack(anchor=tk.W, padx=5, pady=5)
        
    def _setup_help_tab(self, parent):
        """Configura a aba de ajuda"""
        # Informações de ajuda
        help_text = """
SPAdes Help:

SPAdes (St. Petersburg genome assembler) é um montador de genoma desenvolvido 
pelo Centro de Algoritmos Bioinformáticos da Universidade de São Petersburgo.

Recomendações gerais:

1. Escolha do modo:
   • Para bactérias isoladas: use o modo 'isolate' ou 'careful'
   • Para metagenomas: use o modo 'meta'
   • Para transcriptomas: use o modo 'rna'
   • Para plasmídeos: use o modo 'plasmid'
   • Para vírus da família Coronaviridae: use o modo 'corona'

2. Recursos de hardware:
   • Threads: Defina com base no número de núcleos disponíveis
   • Memória: Para um genoma bacteriano típico, 16GB são suficientes
   • Para montagens grandes/complexas, aumente a quantidade de memória

3. K-mers:
   • Para reads curtos (Illumina), valores comuns são 21, 33, 55, 77
   • Para reads longos (PacBio/ONT), valores maiores são recomendados
   • Deixar em branco para usar os valores padrão do SPAdes

4. Resolução de problemas:
   • Erros de memória: Reduza o número de threads ou use menos k-mers
   • Baixa qualidade da montagem: Tente o modo 'careful'
   • Falha na montagem: Verifique a qualidade dos dados de entrada

Para mais informações, consulte o manual oficial do SPAdes:
http://cab.spbu.ru/files/release3.15.5/manual.html
        """
        
        help_frame = ttk.Frame(parent)
        help_frame.pack(fill=tk.BOTH, expand=True)
        
        help_text_widget = tk.Text(help_frame, wrap=tk.WORD, height=20, width=80)
        help_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        scrollbar = ttk.Scrollbar(help_frame, orient=tk.VERTICAL, command=help_text_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        help_text_widget.config(yscrollcommand=scrollbar.set)
        
        help_text_widget.insert(tk.END, help_text)
        help_text_widget.config(state='disabled')
        
    def _toggle_careful(self):
        """Atualiza o modo quando o checkbox 'careful' é alterado"""
        if self.careful.get():
            self.mode.set("careful")
        elif self.mode.get() == "careful":
            self.mode.set("isolate")
            
    def _save_params(self):
        """Salva os parâmetros no config_frame"""
        # Validar threads
        try:
            threads = int(self.threads.get())
            if threads <= 0:
                raise ValueError("Número de threads deve ser maior que zero")
        except (ValueError, TypeError):
            tk.messagebox.showerror("Erro", "Número de threads inválido. Insira um número inteiro maior que zero.")
            return
            
        # Validar memória
        if self.memory.get().strip():
            try:
                memory = int(self.memory.get())
                if memory <= 0:
                    raise ValueError("Memória deve ser maior que zero")
            except (ValueError, TypeError):
                tk.messagebox.showerror("Erro", "Valor de memória inválido. Insira um número inteiro maior que zero ou deixe em branco.")
                return
                
        # Validar k-mers
        if self.kmer.get().strip():
            kmers = self.kmer.get().split(',')
            try:
                for k in kmers:
                    k_value = int(k.strip())
                    if k_value <= 0 or k_value % 2 == 0:
                        raise ValueError("K-mers devem ser números ímpares positivos")
            except (ValueError, TypeError):
                tk.messagebox.showerror("Erro", "Valores de k-mer inválidos. Insira números ímpares positivos separados por vírgula.")
                return
                
        # Verificar se as opções são mutuamente exclusivas
        if self.only_error_correction.get() and self.only_assembler.get():
            tk.messagebox.showerror("Erro", "As opções 'Apenas correção de erros' e 'Apenas montagem' são mutuamente exclusivas.")
            return
            
        # Salvar parâmetros básicos
        self.config_frame.threads.set(self.threads.get())
        self.config_frame.memory.set(self.memory.get())
        self.config_frame.mode.set(self.mode.get())
        self.config_frame.kmer.set(self.kmer.get())
        
        # Fechar diálogo
        self.dialog.destroy()