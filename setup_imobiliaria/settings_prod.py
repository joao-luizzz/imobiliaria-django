"""
Configurações de produção.
Uso: manage.py --settings=setup_imobiliaria.settings_prod
     ou: DJANGO_SETTINGS_MODULE=setup_imobiliaria.settings_prod
"""
from .settings import *  # noqa: F401, F403

# ── Core ────────────────────────────────────────────────────────────────────
DEBUG = False

ALLOWED_HOSTS = config(  # noqa: F405
    'ALLOWED_HOSTS',
    default='127.0.0.1',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# ── Static files — WhiteNoise ────────────────────────────────────────────────
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')  # noqa: F405
STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# ── Segurança ────────────────────────────────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)  # noqa: F405

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True

# ── Banco de dados (mantém SQLite por padrão — trocar no .env para PostgreSQL)
# Para PostgreSQL, adicione ao .env: DATABASE_URL=postgres://user:pass@host:5432/db
# e instale: pip install dj-database-url psycopg2-binary
