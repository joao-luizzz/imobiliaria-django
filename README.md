# Imobiliária — Sistema de Simulação de Financiamento

Sistema web desenvolvido em Django para corretores de imóveis simularem financiamentos, acompanharem propostas e analisarem o poder de compra de clientes.

## Funcionalidades

### Principal
| Módulo | Descrição |
|---|---|
| **Simulador** | SAC ou PRICE com MIP/DFI, gráfico de saldo devedor e salva no histórico |
| **Dashboard** | KPIs gerais, gráfico de simulações por dia, distribuição por status e sistema |
| **Histórico** | Filtros por cliente, status, sistema, tag e período; paginação e exportação |
| **Detalhe** | Tabela completa, comparativo SAC × PRICE, exportação PDF/Excel, link compartilhável e WhatsApp |
| **Oráculo** | Calcula o poder de compra com base em renda, entrada e comprometimento |

### Ferramentas
| Módulo | Descrição |
|---|---|
| **Comparativo** | Comparação visual SAC × PRICE com gráfico de saldo devedor |
| **Amortização Extra** | Impacto de aportes mensais no prazo e nos juros totais |
| **Portabilidade** | Compara taxa atual vs nova e aponta se vale portar |
| **FGTS** | Usa saldo FGTS para reduzir parcela ou prazo |
| **ITBI / Cartório** | Estima ITBI, cartório, avaliação e certidões |
| **IPCA / TR** | Simula impacto da correção monetária sobre o saldo devedor |
| **CET** | Custo Efetivo Total via Newton-Raphson (inclui tarifas e seguros) |
| **Consórcio vs Financiamento** | Compara total pago e parcelas entre as duas modalidades |
| **Refinanciamento** | Compara condições atuais × novas com prazo ajustável |

### Administração (staff only)
| Módulo | Descrição |
|---|---|
| **Usuários** | Criar, editar, ativar/desativar corretores |
| **Relatório PDF** | Relatório gerencial com KPIs, status e últimas simulações |

### API REST
| Endpoint | Método | Descrição |
|---|---|---|
| `/api/simular/` | POST | Retorna tabela de parcelas em JSON |
| `/api/oraculo/` | POST | Retorna poder de compra em JSON |
| `/taxas-bcb/` | GET | Selic, IPCA e CDI em tempo real (BCB) |

## Tecnologias

- Python 3.10+ / Django 4.2+
- Bootstrap 5.3 + Bootstrap Icons
- Chart.js 4.4
- ReportLab (PDF) / openpyxl (Excel)
- WhiteNoise (static files em produção)
- Gunicorn (servidor WSGI)

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
# Edite .env e defina um SECRET_KEY seguro

# 5. Execute as migrações
python manage.py migrate

# 6. Crie o superusuário
python manage.py createsuperuser

# 7. Inicie o servidor
python manage.py runserver
```

Acesse em `http://127.0.0.1:8000/`

## Variáveis de ambiente (`.env`)

| Variável | Descrição | Padrão |
|---|---|---|
| `SECRET_KEY` | Chave secreta do Django | — (obrigatório) |
| `DEBUG` | Modo debug | `True` |
| `ALLOWED_HOSTS` | Hosts permitidos (vírgula) | `127.0.0.1` |
| `SECURE_SSL_REDIRECT` | Redireciona HTTP → HTTPS | `False` |

## Testes

```bash
python manage.py test simulador
```

60 testes cobrindo cálculos SAC/PRICE, model, views e todos os módulos de ferramentas.

## Deploy (produção)

```bash
# Usar settings de produção
export DJANGO_SETTINGS_MODULE=setup_imobiliaria.settings_prod

# Coletar arquivos estáticos
python manage.py collectstatic

# Iniciar com Gunicorn (via Procfile)
gunicorn setup_imobiliaria.wsgi --bind 0.0.0.0:8000 --workers 2
```

## Estrutura do projeto

```
imobiliaria-django/
├── setup_imobiliaria/      # Configurações Django
│   ├── settings.py         # Desenvolvimento
│   └── settings_prod.py    # Produção
├── simulador/              # App principal
│   ├── backends.py         # EmailBackend (login por e-mail)
│   ├── calculos.py         # Funções SAC e PRICE
│   ├── models.py           # Model Simulation (tags, share_token, favorito...)
│   ├── views.py            # Todas as views + API REST + BCB
│   ├── urls.py             # Rotas do app
│   ├── tests.py            # Suite de testes (60 testes)
│   └── templates/simulador/
├── templates/              # base.html (dark mode, sidebar), login, 404, 500
├── static/
│   ├── css/                # CSS customizado
│   └── img/favicon.svg
├── Procfile                # Comando Gunicorn
└── .env.example            # Referência de variáveis
```

## Perfis de acesso

- **Administrador** (`is_staff=True`): acesso completo, vê todas as simulações, gerencia usuários e gera relatório gerencial PDF
- **Corretor**: acessa apenas suas próprias simulações

## Login

Suporta autenticação por **username** ou **e-mail**.
