from django.db import models
from django.contrib.auth.models import User
import uuid


class Simulation(models.Model):
    STATUS_CHOICES = [
        ('novo', 'Novo'),
        ('em_analise', 'Em Análise'),
        ('aprovado', 'Aprovado'),
        ('reprovado', 'Reprovado'),
    ]

    SISTEMA_CHOICES = [
        ('SAC', 'SAC'),
        ('PRICE', 'PRICE'),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='simulacoes')
    cliente = models.CharField(max_length=150)
    valor_imovel = models.DecimalField(max_digits=12, decimal_places=2)
    entrada = models.DecimalField(max_digits=12, decimal_places=2)
    taxa_juros = models.DecimalField(max_digits=5, decimal_places=2)
    prazo_meses = models.PositiveIntegerField()
    sistema = models.CharField(max_length=10, choices=SISTEMA_CHOICES, default='SAC')
    mip_mensal = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    dfi_mensal = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    favorito = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='novo')
    observacoes = models.TextField(blank=True, default='')
    share_token = models.UUIDField(null=True, blank=True, default=None, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Simulação'
        verbose_name_plural = 'Simulações'

    def __str__(self):
        return f"{self.cliente} — R$ {self.valor_imovel} ({self.criado_em:%d/%m/%Y})"

    @property
    def valor_financiado(self):
        return self.valor_imovel - self.entrada
