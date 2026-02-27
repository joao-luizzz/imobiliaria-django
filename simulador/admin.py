from django.contrib import admin
from .models import Simulation


@admin.register(Simulation)
class SimulationAdmin(admin.ModelAdmin):
    list_display = ('cliente', 'usuario', 'valor_imovel', 'entrada', 'sistema', 'status', 'criado_em')
    list_filter = ('status', 'sistema', 'criado_em')
    search_fields = ('cliente', 'usuario__username')
    readonly_fields = ('criado_em',)
    ordering = ('-criado_em',)
