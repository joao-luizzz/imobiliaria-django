# Imobiliária — Sistema de Gestão de Financiamentos

Sistema web desenvolvido em Django para corretores de imóveis simularem financiamentos, gerenciarem clientes, acompanharem propostas em pipeline e analisarem o poder de compra.

## Funcionalidades

### Simulação e análise
| Módulo | Descrição |
|---|---|
| **Simulador** | SAC ou PRICE com MIP/DFI, gráfico de saldo devedor e histórico |
| **Oráculo** | Poder de compra por renda, entrada e comprometimento |
| **Comparativo SAC × PRICE** | Gráfico comparativo entre os dois sistemas |
| **Amortização Extra** | Impacto de aportes mensais no prazo e nos juros |
| **Portabilidade** | Compara taxa atual vs nova, aponta economia |
| **FGTS** | Usa saldo FGTS para reduzir parcela ou prazo |
| **ITBI / Cartório** | Estima ITBI, registro, avaliação e certidões |
| **IPCA / TR** | Simula impacto da correção monetária sobre o saldo |
| **CET** | Custo Efetivo Total via Newton-Raphson |
| **Consórcio vs Financiamento** | Compara total pago e parcelas |
| **Refinanciamento** | Condições atuais × novas com prazo ajustável |

### Ferramentas de análise
| Módulo | Descrição |
|---|---|
| **Comparativo de Bancos** | Calcula 1ª parcela e total pago para 5 bancos simultaneamente |
| **Calculadora MCMV** | Subsídio por faixa de renda (Faixas 1, 1.5, 2, 3) |
| **Renda Mínima** | Cálculo reverso: qual renda é necessária para financiar |
| **Prazo por Idade** | Aplica regra BCB (80 anos e 6 meses) ao prazo desejado |
| **Financiamento IPCA+** | 3 cenários de sensibilidade (otimista, base, pessimista) |
| **Alerta de Taxa** | Toast automático quando Selic/IPCA muda ≥ 0,25pp |

### Gestão
| Módulo | Descrição |
|---|---|
| **Clientes** | CRUD completo com busca e paginação |
| **Pipeline Kanban** | Arraste propostas entre Novo → Em Análise → Aprovado → Reprovado |
| **Metas do Corretor** | Metas mensais de simulações e volume com barra de progresso |

### Administração (staff only)
| Módulo | Descrição |
|---|---|
| **Usuários** | Criar, editar, ativar/desativar corretores |
| **Log de Auditoria** | Registra quem fez o quê e quando (filtro por usuário, data e ação) |
| **Relatório por Corretor** | Ranking de volume, aprovações e taxa de conversão |
| **Relatório PDF** | Relatório gerencial com KPIs e últimas simulações |

### Segurança
| Módulo | Descrição |
|---|---|
| **2FA (TOTP)** | Autenticação em dois fatores via Google Authenticator ou Authy |
| **Bloqueio por tentativas** | 15 min de lockout após 5 tentativas incorretas no 2FA |
| **Login por e-mail** | Autenticação por username ou e-mail |

### API REST
| Endpoint | Método | Descrição |
|---|---|---|
| `/api/simular/` | POST | Tabela de parcelas em JSON |
| `/api/oraculo/` | POST | Poder de compra em JSON |
| `/taxas-bcb/` | GET | Selic, IPCA e CDI em tempo real (BCB) |

## Tecnologias

- Python 3.10+ / Django 5.2
- Bootstrap 5.3 + Bootstrap Icons
- Chart.js 4.4
- ReportLab (PDF) / openpyxl (Excel)
- WhiteNoise (arquivos estáticos)
- Gunicorn (servidor WSGI)
- pyotp (2FA TOTP)
- dj-database-url (suporte a PostgreSQL)

## Instalação local

```bash
# 1. Clone o repositório
git clone https://github.com/joao-luizzz/imobiliaria-django.git
cd imobiliaria-django

# 2. Crie e ative o ambiente virtual
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure as variáveis de ambiente
cp .env.example .env
# Edite .env: gere um SECRET_KEY novo (instruções dentro do arquivo)

# 5. Execute as migrações
python manage.py migrate

# 6. Crie o superusuário
python manage.py createsuperuser

# 7. Inicie o servidor
python manage.py runserver
```

Acesse em `http://127.0.0.1:8000/`

## Variáveis de ambiente (`.env`)

Consulte o arquivo `.env.example` para a lista completa e documentada.

| Variável | Descrição | Dev | Prod |
|---|---|---|---|
| `SECRET_KEY` | Chave secreta do Django | Qualquer valor | Gerar com `get_random_secret_key()` |
| `DEBUG` | Modo debug | `True` | `False` |
| `ALLOWED_HOSTS` | Hosts permitidos (vírgula) | `127.0.0.1,localhost` | `seudominio.com` |
| `DATABASE_URL` | URL do banco | omitir (SQLite) | `postgres://...` |
| `SECURE_SSL_REDIRECT` | Redireciona HTTP→HTTPS | `False` | `True` |

## Testes

```bash
python manage.py test simulador
```

Suíte com 115+ testes cobrindo cálculos SAC/PRICE, models, todas as views (ferramentas, clientes, pipeline, metas, logs, relatórios, 2FA e API REST).

## Deploy (produção)

```bash
# 1. Configurar .env de produção (ver .env.example)
# 2. Instalar dependências
pip install -r requirements.txt

# 3. Coletar arquivos estáticos
python manage.py collectstatic --noinput

# 4. Rodar migrações
python manage.py migrate

# 5. Iniciar com Gunicorn
gunicorn setup_imobiliaria.wsgi --bind 0.0.0.0:$PORT --workers 2
```

O `Procfile` já está configurado para Railway/Render.

## Estrutura do projeto

```
imobiliaria-django/
├── setup_imobiliaria/
│   └── settings.py          # Único arquivo de settings (dev e prod via .env)
├── simulador/
│   ├── backends.py           # Login por e-mail
│   ├── calculos.py           # Funções SAC e PRICE
│   ├── middleware.py         # TwoFactorMiddleware
│   ├── models.py             # Simulation, Cliente, MetaCorretor, AuditLog, UserProfile
│   ├── views.py              # Todas as views + API + BCB
│   ├── urls.py               # Rotas do app
│   ├── tests.py              # Suite de testes
│   └── templates/simulador/
├── templates/                # base.html, login, 404, 500
├── static/
├── .env.example              # Template de variáveis de ambiente
├── Procfile                  # Gunicorn para Railway/Render
└── requirements.txt
```

## Perfis de acesso

- **Administrador** (`is_staff=True`): acesso completo, vê todas as simulações, gerencia usuários, acessa logs e relatórios
- **Corretor**: acessa apenas suas próprias simulações, clientes e metas
