from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


class Cliente(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='clientes')
    nome = models.CharField(max_length=150)
    email = models.EmailField(blank=True, default='')
    telefone = models.CharField(max_length=20, blank=True, default='')
    cpf = models.CharField(max_length=14, blank=True, default='')
    renda_mensal = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    observacoes = models.TextField(blank=True, default='')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return self.nome


class MetaCorretor(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='metas')
    mes = models.PositiveSmallIntegerField()
    ano = models.PositiveSmallIntegerField()
    meta_simulacoes = models.PositiveIntegerField(default=0)
    meta_valor = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        unique_together = ('usuario', 'mes', 'ano')
        ordering = ['-ano', '-mes']
        verbose_name = 'Meta'
        verbose_name_plural = 'Metas'

    def __str__(self):
        return f"{self.usuario.username} — {self.mes:02d}/{self.ano}"


class AuditLog(models.Model):
    usuario = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='logs')
    acao = models.CharField(max_length=100)
    objeto_tipo = models.CharField(max_length=50, blank=True, default='')
    objeto_id = models.IntegerField(null=True, blank=True)
    descricao = models.TextField(blank=True, default='')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'

    def __str__(self):
        return f"{self.usuario} — {self.acao} ({self.criado_em:%d/%m/%Y %H:%M})"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    totp_secret = models.CharField(max_length=32, blank=True, default='')
    totp_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"Perfil 2FA de {self.user.username}"


@receiver(post_save, sender=User)
def criar_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


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
    cliente_ref = models.ForeignKey(Cliente, null=True, blank=True, on_delete=models.SET_NULL, related_name='simulacoes_obj')
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
    tags = models.CharField(max_length=200, blank=True, default='')
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

    @property
    def tags_lista(self):
        return [t.strip() for t in self.tags.split(',') if t.strip()] if self.tags else []
