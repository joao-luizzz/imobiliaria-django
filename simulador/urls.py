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
    path('perfil/', views.perfil, name='perfil'),
    path('usuarios/', views.usuarios_lista, name='usuarios_lista'),
    path('usuarios/novo/', views.usuario_criar, name='usuario_criar'),
    path('usuarios/<int:pk>/editar/', views.usuario_editar, name='usuario_editar'),
    path('usuarios/<int:pk>/toggle/', views.usuario_toggle_ativo, name='usuario_toggle_ativo'),
    path('s/<uuid:token>/', views.simulacao_publica, name='simulacao_publica'),
]
