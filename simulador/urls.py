from django.urls import path
from . import views

app_name = 'simulador'

urlpatterns = [
    path('', views.simular, name='simular'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('historico/', views.historico, name='historico'),
    path('historico/exportar/', views.exportar_historico, name='exportar_historico'),
    path('historico/<int:pk>/', views.detalhe_simulacao, name='detalhe_simulacao'),
    path('historico/<int:pk>/editar/', views.editar_simulacao, name='editar_simulacao'),
    path('historico/<int:pk>/excluir/', views.excluir_simulacao, name='excluir_simulacao'),
    path('historico/<int:pk>/status/', views.alterar_status, name='alterar_status'),
    path('historico/<int:pk>/favorito/', views.toggle_favorito, name='toggle_favorito'),
    path('historico/<int:pk>/pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('historico/<int:pk>/excel/', views.exportar_excel, name='exportar_excel'),
    path('historico/<int:pk>/link/', views.gerar_link, name='gerar_link'),
    path('oraculo/', views.oraculo, name='oraculo'),
    path('comparativo/', views.comparativo, name='comparativo'),
    path('amortizacao-extra/', views.amortizacao_extra, name='amortizacao_extra'),
    path('portabilidade/', views.portabilidade, name='portabilidade'),
    path('fgts/', views.fgts, name='fgts'),
    path('itbi/', views.itbi, name='itbi'),
    path('ipca-tr/', views.ipca_tr, name='ipca_tr'),
    path('cet/', views.cet, name='cet'),
    path('consorcio/', views.consorcio, name='consorcio'),
    path('refinanciamento/', views.refinanciamento, name='refinanciamento'),
    path('relatorio-pdf/', views.relatorio_pdf, name='relatorio_pdf'),
    path('taxas-bcb/', views.taxas_bcb, name='taxas_bcb'),
    path('api/simular/', views.api_simular, name='api_simular'),
    path('api/oraculo/', views.api_oraculo, name='api_oraculo'),
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/2fa/', views.setup_2fa, name='setup_2fa'),
    path('2fa/verificar/', views.verificar_2fa, name='verificar_2fa'),
    path('usuarios/', views.usuarios_lista, name='usuarios_lista'),
    path('usuarios/novo/', views.usuario_criar, name='usuario_criar'),
    path('usuarios/<int:pk>/editar/', views.usuario_editar, name='usuario_editar'),
    path('usuarios/<int:pk>/toggle/', views.usuario_toggle_ativo, name='usuario_toggle_ativo'),
    path('s/<uuid:token>/', views.simulacao_publica, name='simulacao_publica'),
    # Novas ferramentas
    path('comparativo-bancos/', views.comparativo_bancos, name='comparativo_bancos'),
    path('mcmv/', views.mcmv, name='mcmv'),
    path('renda-minima/', views.renda_minima, name='renda_minima'),
    path('prazo-idade/', views.prazo_idade, name='prazo_idade'),
    path('financiamento-ipca/', views.financiamento_ipca, name='financiamento_ipca'),
    # Clientes
    path('clientes/', views.clientes_lista, name='clientes_lista'),
    path('clientes/novo/', views.cliente_criar, name='cliente_criar'),
    path('clientes/<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('clientes/<int:pk>/excluir/', views.cliente_excluir, name='cliente_excluir'),
    path('clientes/<int:pk>/', views.cliente_detalhe, name='cliente_detalhe'),
    # Pipeline
    path('pipeline/', views.pipeline, name='pipeline'),
    path('pipeline/<int:pk>/mover/', views.mover_card, name='mover_card'),
    # Metas
    path('metas/', views.metas, name='metas'),
    path('metas/nova/', views.meta_criar, name='meta_criar'),
    path('metas/<int:pk>/editar/', views.meta_editar, name='meta_editar'),
    path('metas/<int:pk>/excluir/', views.meta_excluir, name='meta_excluir'),
    # Admin
    path('logs/', views.logs_auditoria, name='logs_auditoria'),
    path('relatorio-corretores/', views.relatorio_corretores, name='relatorio_corretores'),
]
