# Imobiliária — Sistema de Simulação de Financiamento

Sistema web desenvolvido em Django para corretores de imóveis simularem financiamentos, acompanharem propostas e analisarem o poder de compra de clientes.

## Funcionalidades

| Módulo | Descrição |
|---|---|
| **Simulador** | Calcula parcelas SAC ou PRICE com tabela completa e salva o histórico |
| **Dashboard** | KPIs gerais, gráfico de simulações por mês e mapa de calor |
| **Histórico** | Lista com filtros por cliente/status/sistema, paginação e exportação |
| **Detalhe** | Tabela completa de parcelas, exportação PDF e Excel por simulação |
| **Comparativo** | Comparação visual SAC × PRICE com gráfico de saldo devedor (Chart.js) |
| **Oráculo** | Calcula o poder de compra com base em renda, entrada e comprometimento |
| **Perfil** | Edição de dados pessoais e troca de senha |
| **Usuários** | Gestão de corretores pelo administrador (criar, editar, ativar/desativar) |

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
git clone https://github.com/SEU_USUARIO/imobiliaria-django.git
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

43 testes cobrindo cálculos SAC/PRICE, model e views.

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
│   ├── calculos.py         # Funções SAC e PRICE
│   ├── models.py           # Model Simulation
│   ├── views.py            # Todas as views
│   ├── urls.py             # Rotas do app
│   ├── tests.py            # Suite de testes
│   └── templates/simulador/
├── templates/              # base.html, login, 404, 500
├── static/css/             # CSS customizado
├── Procfile                # Comando Gunicorn
└── .env.example            # Referência de variáveis
```

## Perfis de acesso

- **Administrador** (`is_staff=True`): acesso completo, vê todas as simulações e gerencia usuários
- **Corretor**: acessa apenas suas próprias simulações
