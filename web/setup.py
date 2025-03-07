#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de instalação para SPAdes Master Web
"""

from setuptools import setup, find_packages
import os
import platform
import shutil

# Verificar ou criar diretórios necessários
for directory in ['temp', 'results', 'logs']:
    os.makedirs(directory, exist_ok=True)

# Ler versão do arquivo settings.py
version = '1.0.0'  # Valor padrão
try:
    with open('config/settings.py', 'r') as f:
        for line in f:
            if line.startswith('APP_VERSION'):
                version = line.split('=')[1].strip().strip('"\'')
                break
except:
    pass

# Ler o README.md para long_description
try:
    with open('README.md', 'r', encoding='utf-8') as f:
        long_description = f.read()
except:
    long_description = 'SPAdes Master Web - Interface para gerenciamento de montagens SPAdes'

# Criar arquivos de atalho do desktop para Linux
def create_linux_desktop_file():
    try:
        # Verificar se o diretório de aplicações existe
        desktop_dir = os.path.expanduser('~/.local/share/applications')
        os.makedirs(desktop_dir, exist_ok=True)
        
        # Caminho atual da aplicação
        app_path = os.path.abspath(os.path.dirname(__file__))
        
        # Criar o arquivo .desktop
        desktop_file = os.path.join(desktop_dir, 'spades-master.desktop')
        
        # Criar conteúdo do arquivo
        content = f"""[Desktop Entry]
Type=Application
Name=SPAdes Master Web
Comment=Interface web para gerenciamento de montagens SPAdes
Exec=python3 {os.path.join(app_path, 'app_launcher.py')}
Terminal=false
Icon={os.path.join(app_path, 'frontend/static/img/spades_icon.png')}
Categories=Science;Biology;
Keywords=bioinformatics;genomics;assembly;spades;
"""
        
        # Escrever o arquivo
        with open(desktop_file, 'w') as f:
            f.write(content)
        
        # Tornar o arquivo executável
        os.chmod(desktop_file, 0o755)
        
        print(f"Arquivo de desktop criado em {desktop_file}")
        return True
    except Exception as e:
        print(f"Erro ao criar arquivo de desktop: {str(e)}")
        return False

# Criar atalho no menu iniciar para Windows
def create_windows_shortcut():
    try:
        import win32com.client
        
        # Caminho para o menu iniciar
        start_menu = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs", "SPAdes Master Web")
        os.makedirs(start_menu, exist_ok=True)
        
        # Caminho atual da aplicação
        app_path = os.path.abspath(os.path.dirname(__file__))
        app_launcher = os.path.join(app_path, 'app_launcher.py')
        icon_path = os.path.join(app_path, 'frontend/static/img/spades_icon.ico')
        
        # Criar atalho
        shortcut_path = os.path.join(start_menu, "SPAdes Master Web.lnk")
        
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.TargetPath = "pythonw"
        shortcut.Arguments = app_launcher
        shortcut.WorkingDirectory = app_path
        shortcut.IconLocation = icon_path
        shortcut.Description = "Interface web para gerenciamento de montagens SPAdes"
        shortcut.save()
        
        print(f"Atalho criado em {shortcut_path}")
        return True
    except Exception as e:
        print(f"Erro ao criar atalho: {str(e)}")
        return False

# Procurar por ícones e arquivos de desktop específicos da plataforma
icon_files = []
desktop_files = []

# Configurar a instalação
setup(
    name="spades-master-web",
    version=version,
    author="SPAdes Master Team",
    author_email="example@example.com",
    description="Interface web para gerenciamento de montagens SPAdes",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/spades-master-web",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "flask>=2.0.0",
        "flask-socketio>=5.0.0",
        "paramiko>=2.7.2",
        "scp>=0.14.0",
        "eventlet>=0.30.0",
        "cryptography>=36.0.0",
    ],
    entry_points={
        'console_scripts': [
            'spades-master-web=app:main',
        ],
    },
    data_files=[(os.path.join(os.path.expanduser('~'), '.local/share/applications'), desktop_files)],
)

# Executar funções específicas de plataforma após a instalação
if platform.system() == "Linux":
    create_linux_desktop_file()
elif platform.system() == "Windows":
    try:
        import win32com.client
        create_windows_shortcut()
    except ImportError:
        print("Módulo win32com não encontrado. Atalho não foi criado.")
        print("Instale-o com: pip install pywin32")