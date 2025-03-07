# SPAdes Master Web

SPAdes Master Web é uma interface web moderna para gerenciar, executar e monitorar montagens genômicas utilizando o [SPAdes](https://github.com/ablab/spades) (St. Petersburg genome assembler) em servidores remotos.

![SPAdes Master Web Screenshot](frontend/static/img/screenshot.png)

## Características Principais

- **Interface Web Responsiva**: Acesse a ferramenta de qualquer dispositivo com um navegador.
- **Gerenciamento de perfis de servidor**: Salve e administre múltiplas configurações de servidores.
- **Conexão SSH simplificada**: Conecte-se facilmente a servidores remotos sem precisar usar comandos de terminal.
- **Envio automático de arquivos**: Envie seus arquivos FASTQ para o servidor com apenas alguns cliques.
- **Configuração personalizada do SPAdes**: Configure todos os parâmetros importantes do SPAdes através da interface gráfica.
- **Monitoramento em tempo real**: Acompanhe o progresso e uso de recursos durante a execução via WebSockets.
- **Visualização de resultados**: Analise os resultados da montagem diretamente na interface web.
- **Download seletivo**: Baixe apenas os arquivos importantes ou todos os resultados conforme necessário.

## Requisitos

- Python 3.6 ou superior
- SPAdes instalado no servidor remoto

## Instalação

### Método 1: Instalação Simples

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/spades-master-web.git
cd spades-master-web

# Criar ambiente virtual (opcional, mas recomendado)
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Executar a aplicação
python app.py
```

### Método 2: Instalação como Aplicativo

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/spades-master-web.git
cd spades-master-web

# Instalar o aplicativo
pip install -e .
```

## Uso

### Executando a Aplicação Web

```bash
# Método 1: Executar como script
python app.py

# Método 2: Executar como aplicativo
python app_launcher.py
```

Por padrão, a aplicação será executada em http://127.0.0.1:5000

### Argumentos de Linha de Comando

```
python app.py --help
```

Opções disponíveis:
- `--host`: Endereço IP para associar o servidor (padrão: 127.0.0.1)
- `--port`: Porta para o servidor web (padrão: 5000)
- `--no-browser`: Não abrir o navegador automaticamente
- `--debug`: Executar em modo debug

### Fluxo de Trabalho Típico

1. **Configurar um Perfil de Servidor**
   - Acesse "Perfis de Servidor"
   - Clique em "Novo Perfil"
   - Preencha as informações de conexão SSH
   - Salve o perfil

2. **Executar uma Montagem**
   - Vá para "Execução"
   - Selecione o perfil e conecte-se ao servidor
   - Faça upload dos arquivos FASTQ
   - Configure os parâmetros do SPAdes
   - Inicie a execução

3. **Monitorar o Progresso**
   - Acompanhe o uso de CPU e memória
   - Veja o log de execução em tempo real
   - Verifique o tempo decorrido e a fase atual

4. **Visualizar os Resultados**
   - Baixe os arquivos importantes ao finalizar
   - Acesse "Resultados" para visualizar estatísticas
   - Analise os contigs, scaffolds e outras métricas
   - Faça download de arquivos específicos

## Estrutura do Projeto

```
spades-master-web/
├── backend/                    # Backend Python
│   ├── __init__.py
│   ├── app.py                  # Aplicação Flask principal
│   ├── api/                    # Endpoints da API
│   ├── services/               # Serviços
│   ├── models/                 # Modelos
│   └── utils/                  # Utilitários
├── frontend/                   # Frontend Web
│   ├── static/                 # Arquivos estáticos
│   │   ├── css/
│   │   ├── js/
│   │   └── img/                # Imagens e ícones
│   └── templates/              # Templates HTML
├── config/                     # Configurações
├── logs/                       # Logs da aplicação
├── results/                    # Resultados baixados
├── temp/                       # Arquivos temporários
├── app.py                      # Ponto de entrada da aplicação web
├── app_launcher.py             # Launcher para aplicativo standalone
├── requirements.txt            # Dependências
├── setup.py                    # Script de instalação
└── README.md                   # Este arquivo
```

## Configuração Personalizada

### Caminhos e Diretórios

Os diretórios padrão podem ser modificados no arquivo `config/settings.py`:

```python
# Exemplos de configuração
APP_NAME = "SPAdes Master Web"
APP_VERSION = "1.0.0"

# Diretórios de configuração
def get_config_dir():
    """Retorna o diretório de configuração apropriado para o sistema operacional"""
    if platform.system() == "Windows":
        return os.path.join(os.environ["APPDATA"], APP_NAME)
    elif platform.system() == "Darwin":  # macOS
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    else:  # Linux/Unix
        return os.path.join(os.path.expanduser("~"), ".config", APP_NAME)
```

## Resolução de Problemas

### Problemas de Conexão SSH

Se ocorrerem problemas de conexão SSH:
1. Verifique se o servidor está acessível (ping)
2. Confirme se as credenciais estão corretas
3. Verifique restrições de firewall
4. Teste a conexão SSH manualmente no terminal

### O SPAdes não é encontrado automaticamente

Se o SPAdes não for encontrado automaticamente no servidor:
1. Verifique se o SPAdes está instalado e acessível no PATH
2. Tente especificar manualmente o caminho completo para o executável SPAdes
3. Verifique as permissões do diretório onde o SPAdes está instalado

### Erros na Execução do SPAdes

Se o SPAdes falhar durante a execução:
1. Verifique os logs na interface
2. Confirme se o SPAdes está instalado corretamente no servidor
3. Verifique se há memória e espaço em disco suficientes
4. Tente reduzir o número de threads ou a quantidade de memória alocada

## Contribuindo

Contribuições são bem-vindas! Por favor, sinta-se à vontade para abrir issues ou enviar pull requests.

1. Faça fork do repositório
2. Crie sua branch de feature (`git checkout -b feature/sua-feature`)
3. Faça commit das suas mudanças (`git commit -m 'Adiciona alguma feature'`)
4. Faça push para a branch (`git push origin feature/sua-feature`)
5. Abra um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

## Créditos

- SPAdes Master Web é desenvolvido e mantido por [Seu Nome]
- [SPAdes](https://github.com/ablab/spades) - St. Petersburg genome assembler

## Citação

Se você usar o SPAdes Master Web em sua pesquisa, por favor cite:

```
[Seu Nome], et al. (2025). SPAdes Master Web: A web interface for SPAdes genome assembler. [URL do seu repositório]
```

E não se esqueça de citar também o SPAdes:

```
Bankevich, A., et al. (2012). SPAdes: A New Genome Assembly Algorithm and Its Applications to Single-Cell Sequencing. Journal of Computational Biology, 19(5), 455-477.
```