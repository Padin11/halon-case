# Halon Financeiro - Sistema de Gestão Corporativa (SaaS)

> **Case Técnico:** Plataforma de alta performance para controle de fluxo de caixa, contas a pagar/receber e inteligência financeira. Projetado com foco em escalabilidade, segurança (OWASP) e arquitetura limpa.

-----

## Visão Geral e Arquitetura

Este projeto não foi concebido apenas como um CRUD, mas como uma base sólida para um produto SaaS financeiro. As principais decisões arquiteturais incluem:

  * **Backend 100% Assíncrono:** Utilização de `async/await` desde o endpoint (FastAPI) até o driver de banco de dados (`asyncpg`), permitindo alta concorrência sem bloqueio de I/O.
  * **Domain-Driven Design (Simplificado):** Separação clara entre **Rotas** (Controladores), **Schemas** (Contratos/DTOs), **Modelos** (Entidades) e **Serviços** (Regras de Negócio), facilitando manutenção e testes.
  * **Analytics no Database:** Para evitar gargalos de memória no Python, toda a agregação de dados para Dashboards (Somas, Agrupamentos, Rankings) é realizada via queries SQL otimizadas (`SUM`, `CASE`, `GROUP BY`) através do SQLAlchemy.
  * **Frontend Modular (Sem Build):** Utilização de **ES Modules** nativos do navegador. Isso elimina a complexidade de ferramentas de build (Webpack/Vite) para o MVP, mantendo o código organizado em módulos (`api.js`, `ui.js`, `main.js`) e performático.

-----

## Stack Tecnológica

### Backend

  * **Linguagem:** Python 3.11
  * **Framework:** FastAPI (Pydantic v2 para validação rigorosa)
  * **ORM:** SQLAlchemy 2.0 (Sintaxe moderna e tipada)
  * **Auth:** Python-Jose (JWT) + Passlib (Bcrypt)

### Banco de Dados

  * **SGBD:** PostgreSQL 15
  * **Driver:** Asyncpg (Alta performance)
  * **Modelagem:** Relacional normalizada com índices estratégicos em colunas de busca e data.

### Frontend

  * **Core:** Vanilla JS (ES6+) + Axios
  * **UI Kit:** Bootstrap 5
  * **Visualização:** Chart.js (Gráficos interativos)
  * **Server:** Nginx Alpine (Container leve para servir estáticos)

### Infraestrutura

  * **Containerização:** Docker & Docker Compose

-----

## Instalação e Execução

### Pré-requisitos

  * Docker Engine e Docker Compose instalados.

### Passo a Passo

### 1. Clone e Configure

1.  Clone o repositório:
    ```bash
    git clone https://github.com/Padin11/halon-case.git
    cd halon-case
    ```
2.  **Configuração de Ambiente (Automatizado):** O arquivo `docker-compose.yml` está configurado para **copiar automaticamente** o `.env.example` para `.env` na primeira vez que você executar o Docker.

### 2. Suba os Containers
```bash

1.  **Configuração de Ambiente (.env):**
    O projeto já possui um arquivo `.env` configurado para o ambiente Docker local padrão.

      * *Banco:* `financeiro_db`
      * *Usuário:* `usuario_fin`
      * *Senha:* `senha_segura123`
      * *Secret Key:* Configurada para dev.

2.  **Subir a Aplicação:**
    Execute o comando de orquestração:

    ```bash
    docker compose up --build -d
    ```

    *Aguarde cerca de 30s na primeira execução para o banco inicializar e a API subir.*

3.  **Acessar:**

      * **Frontend:** [http://localhost:3000]
      * **API Docs:** [http://localhost:8000/docs]

-----

## Gerador de Dados (Seed)

Para testar a performance dos dashboards e simular um ambiente real, o projeto inclui uma **CLI (Command Line Interface)** interativa.

**Como usar:**
No terminal, execute o script Python dentro do container da API:

```bash
docker compose exec api python -m app.Popular
```

**Funcionalidades da CLI:**

1.  **Verificação de Admin:** Detecta se já existe administrador. Se não, guia a criação segura.
2.  **Simulação de Carga:**
      * Cria contas bancárias em bancos reais (Itaú, Nubank, etc).
      * Gera centenas de Clientes e Fornecedores com nomes realistas.
      * Gera milhares de lançamentos (Títulos) com distribuição inteligente de datas (passado/futuro) e status (pago/vencido/pendente).
      * Vincula anexos fictícios aos lançamentos.

> **Recomendação:** Gere pelo menos **500 registros** para visualizar os gráficos e rankings.

-----

## Documentação da API

A API segue o padrão **RESTful** e é documentada automaticamente via **OpenAPI (Swagger)**.

### Endpoints Principais

| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `POST` | `/auth/login` | Autenticação OAuth2 (Retorna JWT) |
| `POST` | `/auth/registro` | Criação de novos usuários |
| `POST` | `/titulos` | Criação de título (Suporta parcelamento automático) |
| `GET` | `/titulos` | Listagem paginada de títulos |
| `GET` | `/dashboard/resumo` | KPIs financeiros (Saldo, Inadimplência) |
| `GET` | `/dashboard/ranking` | Top Devedores e Credores |
| `GET` | `/dashboard/busca-contato` | Autocomplete inteligente de contatos |

-----

## Frontend e Dashboard

O Frontend foi desenvolvido como uma **SPA (Single Page Application)** leve.

### Funcionalidades

  * **Autenticação:** Login seguro com armazenamento de token e redirecionamento automático.
  * **Dashboard Executivo:**
      * **KPIs:** Cards com valores formatados (R$) e coloração semântica (Vermelho para prejuízo/risco).
      * **Gráficos:** Fluxo de Caixa mensal e Distribuição por Categoria.
  * **Rankings:** Listas de maiores devedores e credores.
  * **Busca Inteligente:** Barra de pesquisa com *debounce* (atraso na digitação) que consulta a API e exibe a situação financeira de um cliente específico em tempo real.
  * **Input:** Modal para lançamento rápido de títulos com seleção dinâmica de categorias.

-----

## Segurança e Boas Práticas

A segurança foi uma prioridade desde a concepção da arquitetura (Security by Design):

1.  **Proteção contra SQL Injection:** Uso estrito de ORM (SQLAlchemy) para todas as interações com o banco.
2.  **Proteção contra XSS (Cross-Site Scripting):** No Frontend, todo dado vindo do usuário é renderizado via `textContent` (e não `innerHTML`), impedindo a execução de scripts maliciosos injetados.
3.  **Hashing de Senhas:** Nenhuma senha é salva em texto plano. Utilizamos **Bcrypt**, um algoritmo lento e com *salt*, resistente a ataques de *rainbow table*.
4.  **Fail Fast:** O Backend recusa iniciar se variáveis críticas de ambiente (como `SECRET_KEY` em produção) não estiverem presentes.
5.  **CORS Configurado:** A API aceita requisições apenas das origens confiáveis definidas no middleware.

-----



## Ferramentas CLI (Seed e Administração)

### 1\. Manutenção de Usuário (Troca de Senha) 

Utilize `admin.py` para realizar operações de manutenção de segurança, como a **troca de senha** de qualquer usuário, fora do fluxo da API.

```bash
docker compose exec api python -m app.admin
```

*Siga as instruções na tela para informar o login usuário e a nova senha a ser aplicada.*

-----

## Testes Automatizados

O projeto conta com testes unitários focados nas regras de negócio críticas, como o algoritmo de parcelamento financeiro (tratamento de dízimas e datas).

**Para rodar os testes:**

```bash
# Instala dependências de teste (caso não estejam no container) e executa
docker compose exec api pip install pytest && docker compose exec api pytest
```

-----

## Estrutura do projeto

```text
/
├── app/                        # Backend (Python)
│   ├── __init__.py
│   ├── main.py                 # Entrypoint da API e Configs
│   ├── database.py             # Conexão Async com Postgres
│   ├── modelo.py               # Tabelas do Banco (SQLAlchemy)
│   ├── schemas.py              # Validação de Dados (Pydantic)
│   ├── rotas.py                # Endpoints (Controllers)
│   ├── servicos.py             # Regras de Negócio (Parcelamento)
│   ├── seguranca.py            # Criptografia e JWT
│   ├── deps.py                 # Dependências e Middlewares
│   └── Popular.py              # Script CLI de Seed
├── frontend/                   # Frontend (Nginx)
│   ├── css/                    # Estilos
│   ├── js/                     # Lógica Modular
│   │   ├── api.js              # Camada de Rede (Axios)
│   │   ├── ui.js               # Manipulação do DOM
│   │   └── main.js             # Controlador Principal
│   ├── index.html              # Interface
│   └── Dockerfile              # Configuração do Nginx
├── tests/                      # Testes Unitários
├── docker-compose.yml          # Orquestração dos Containers
├── Dockerfile                  # Configuração da Imagem Python
├── requirements.txt            # Dependências Python
└── .env                        # Variáveis de Ambiente (Credenciais)
```

