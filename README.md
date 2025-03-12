# SPAdes Master v1.2.1

Uma interface gráfica para gerenciar montagens genômicas com [SPAdes](https://github.com/ablab/spades) em servidores remotos.

![SPAdes Master Screenshot](media/spades_master_screenshot.png)

## Descrição

SPAdes Master é uma aplicação desktop desenvolvida em Python/Tkinter que permite gerenciar execuções remotas do montador de genomas SPAdes em servidores Linux via SSH. A ferramenta facilita o upload de arquivos FASTQ, configuração de parâmetros, monitoramento de execução e download de resultados, tudo através de uma interface gráfica amigável.

## Principais Funcionalidades

- **Gerenciamento de Perfis de Servidor**: Salve e reutilize configurações de conexão SSH para diferentes servidores.
- **Upload de Arquivos**: Envie facilmente arquivos FASTQ para o servidor.
- **Configuração do SPAdes**: Interface intuitiva para definir parâmetros do SPAdes (threads, memória, k-mers, etc).
- **Múltiplos Modos de Montagem**: Suporte para todos os modos do SPAdes (isolate, careful, meta, rna, plasmid, etc).
- **Monitoramento em Tempo Real**: Visualize o status da execução, uso de CPU/memória e logs em tempo real.
- **Download de Resultados**: Baixe apenas os arquivos importantes ou o conjunto completo de resultados.
- **Interface Responsiva**: Design moderno e adaptável a diferentes tamanhos de tela.
- **Terminal SSH Integrado**: Acesse diretamente o servidor com um clique.

## Requisitos de Sistema

- Python 3.6+
- Bibliotecas Python:
  - paramiko (>=2.7.2)
  - scp (>=0.14.0)
  - cryptography (>=36.0.0)
  - ttkthemes (>=3.2.2)
- Conexão com internet para acessar servidores remotos

## Instalação

### A partir do código-fonte:

1. Clone o repositório ou baixe os arquivos-fonte
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Execute o aplicativo:
   ```
   python main.py
   ```

### Usando o executável (Windows):

1. Baixe o arquivo executável da página de releases
2. Execute o arquivo `SPAdesMaster.exe`

## Criando um Executável

Para gerar um executável, o projeto inclui um arquivo spec para PyInstaller:

```
pyinstaller SPAdesMaster.spec
```

O executável será criado na pasta `dist/SPAdesMaster`.

## Guia de Uso

### 1. Configuração do Servidor

- Na aba "Configuração", crie um novo perfil de servidor ou selecione um existente
- Informe o endereço do servidor, porta SSH, usuário e senha (ou arquivo de chave SSH)
- Clique em "Testar Conexão" para verificar se as credenciais estão corretas

### 2. Configuração da Montagem

- Selecione os arquivos FASTQ de entrada (R1 e R2)
- Especifique o diretório remoto para armazenar os arquivos
- Configure os parâmetros do SPAdes (threads, memória, modo, etc)
- Para opções avançadas, clique no menu "SPAdes" > "Configurar Parâmetros"

### 3. Execução

- Na aba "Execução e Monitoramento", clique em "Conectar ao Servidor"
- Clique em "Preparar e Enviar Arquivos" para enviar os arquivos FASTQ
- Inicie a montagem clicando em "Iniciar SPAdes"
- Monitore o progresso, uso de recursos e logs no painel unificado

### 4. Resultados

- Na aba "Resultados", baixe os arquivos gerados pelo SPAdes
- Opção para baixar apenas arquivos importantes ou todos os arquivos
- Visualize estatísticas da montagem como número de contigs, N50, etc
- Abra a pasta de resultados para análise posterior

## Solução de Problemas

### SPAdes não encontrado no servidor

Se o SPAdes não for encontrado automaticamente:
1. Será exibido um diálogo para especificar manualmente o caminho
2. Informe o caminho completo para o executável do SPAdes (ex: `/usr/local/bin/spades.py`)
3. O sistema irá verificar se o caminho é válido e armazenar para uso futuro

### Falha na conexão SSH

- Verifique se as credenciais (usuário/senha ou chave SSH) estão corretas
- Confirme se o servidor está acessível e se a porta SSH está aberta
- Verifique se há restrições de firewall ou limitações de acesso SSH

### Monitoramento de Processos

Os processos do SPAdes são monitorados automaticamente. Se a aplicação detectar que um processo não está mais rodando:
1. O status será atualizado para "SPAdes concluído"
2. Será verificado se o arquivo de scaffolds foi gerado com sucesso
3. Você será notificado para que possa proceder com o download dos resultados

## Atribuições

- SPAdes: [Center for Algorithmic Biotechnology](http://cab.spbu.ru/software/spades/)
- Ícone: Criado para o projeto SPAdes Master

## Licença

Este software é distribuído sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## Contato

Para dúvidas, sugestões ou reportar problemas, abra uma issue no repositório do projeto.
