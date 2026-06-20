# Sistema Raízes do Nordeste - API Back-end

Interface de programação de aplicativos (API) desenvolvida como solução back-end para o sistema Raízes do Nordeste, estruturada com base nas melhores práticas de arquitetura de software e design RESTful.

## Características do Projeto

* **Arquitetura em 4 Camadas**: Divisão clara de responsabilidades entre as camadas de Domínio (Domain), Aplicação (Application), Infraestrutura (Infrastructure) e Interface (API).
* **Persistência Real**: Integração com banco de dados SQLite utilizando o SQLAlchemy ORM, garantindo operações CRUD reais e consistentes.
* **Carga Inicial Automática (Seed)**: Inicialização inteligente que popula a base de dados com itens de teste do cardápio logo no primeiro início do servidor.
* **Validação de Multicanalidade**: Controle estrito e padronizado do contrato de pedidos, restringindo as entradas aos canais permitidos (APP, TOTEM, BALCAO, PICKUP, WEB).
* **Segurança Baseada em Perfis (RBAC)**: Mecanismo de simulação de autenticação com distinção de privilégios para perfis de Cliente e Administrador.
* **Tratamento Global de Erros**: Respostas JSON padronizadas para qualquer falha, contendo chaves consistentes para rastreabilidade (error, message, details, timestamp, path).

## Como Executar o Ambiente Local

1. Clonar o repositório:
   git clone https://github.com/a-f-mad/api-raizes-nordeste.git
   cd api-raizes-nordeste

2. Criar o ambiente virtual (venv):
   python -m venv .venv

3. Ativar o ambiente virtual:
   * No Windows (Prompt de Comando ou PowerShell):
     .venv\Scripts\activate
   * No Linux / macOS:
     source .venv/bin/activate

4. Instalar as dependências do projeto:
   pip install -r requirements.txt

5. Iniciar o servidor de desenvolvimento:
   python main.py

6. Acessar a documentação:
   Com o servidor rodando, abra o navegador e acesse a interface interativa do Swagger UI:
   http://127.0.0.1:8000/docs

## Credenciais de Teste (Parâmetro authorization)

Para testar a segurança e as regras de negócio diretamente pela interface do Swagger, utilize os seguintes parâmetros na URL (Query):

* Perfil Cliente: Bearer TOKEN_CLIENTE (Permite realizar pedidos)
* Perfil Administrador: Bearer TOKEN_ADMIN (Permite gerenciar produtos no CRUD)
