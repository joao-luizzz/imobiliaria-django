from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User

from .models import Simulation
from .calculos import calcular_sac, calcular_price


# ── Cálculos ──────────────────────────────────────────────────────────────────

class TestCalcularSAC(TestCase):

    def test_numero_de_parcelas(self):
        result = calcular_sac(100000, 12, 120)
        self.assertEqual(len(result), 120)

    def test_amortizacao_constante(self):
        result = calcular_sac(120000, 9, 12)
        amortizacoes = {float(p['amortizacao']) for p in result}
        self.assertEqual(len(amortizacoes), 1)
        self.assertAlmostEqual(list(amortizacoes)[0], 120000 / 12, places=2)

    def test_saldo_final_zero(self):
        result = calcular_sac(100000, 10, 120)
        self.assertAlmostEqual(float(result[-1]['saldo_devedor']), 0, places=1)

    def test_parcelas_decrescentes(self):
        result = calcular_sac(100000, 12, 12)
        valores = [float(p['valor']) for p in result]
        self.assertTrue(all(valores[i] >= valores[i + 1] for i in range(len(valores) - 1)))

    def test_prazo_zero_retorna_lista_vazia(self):
        self.assertEqual(calcular_sac(100000, 10, 0), [])

    def test_taxa_zero(self):
        result = calcular_sac(12000, 0, 12)
        self.assertEqual(len(result), 12)
        self.assertAlmostEqual(float(result[0]['juros']), 0, places=2)
        self.assertAlmostEqual(float(result[0]['valor']), 1000, places=2)

    def test_numero_sequencial(self):
        result = calcular_sac(60000, 6, 6)
        self.assertEqual([p['numero'] for p in result], [1, 2, 3, 4, 5, 6])


class TestCalcularPRICE(TestCase):

    def test_numero_de_parcelas(self):
        result = calcular_price(100000, 12, 120)
        self.assertEqual(len(result), 120)

    def test_parcelas_iguais(self):
        result = calcular_price(100000, 12, 120)
        self.assertEqual(len({p['valor'] for p in result}), 1)

    def test_saldo_final_zero(self):
        result = calcular_price(100000, 10, 120)
        self.assertAlmostEqual(float(result[-1]['saldo_devedor']), 0, places=1)

    def test_prazo_zero_retorna_lista_vazia(self):
        self.assertEqual(calcular_price(100000, 10, 0), [])

    def test_taxa_zero(self):
        result = calcular_price(12000, 0, 12)
        self.assertEqual(len(result), 12)
        self.assertAlmostEqual(float(result[0]['valor']), 1000, places=2)

    def test_total_pago_maior_que_financiado(self):
        result = calcular_price(100000, 10, 120)
        self.assertGreater(sum(float(p['valor']) for p in result), 100000)

    def test_numero_sequencial(self):
        result = calcular_price(60000, 6, 6)
        self.assertEqual([p['numero'] for p in result], [1, 2, 3, 4, 5, 6])


# ── Model ─────────────────────────────────────────────────────────────────────

class TestSimulationModel(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('testuser', password='testpass')

    def _make(self, **kw):
        d = dict(usuario=self.user, cliente='Teste', valor_imovel=300000,
                 entrada=60000, taxa_juros='0.75', prazo_meses=360, sistema='SAC')
        d.update(kw)
        return Simulation.objects.create(**d)

    def test_valor_financiado(self):
        sim = self._make(valor_imovel=300000, entrada=60000)
        self.assertEqual(sim.valor_financiado, Decimal('240000'))

    def test_status_default_novo(self):
        self.assertEqual(self._make().status, 'novo')

    def test_str_contem_cliente(self):
        self.assertIn('João Silva', str(self._make(cliente='João Silva')))

    def test_sistema_sac(self):
        self.assertEqual(self._make(sistema='SAC').sistema, 'SAC')

    def test_sistema_price(self):
        self.assertEqual(self._make(sistema='PRICE').sistema, 'PRICE')


# ── Views ─────────────────────────────────────────────────────────────────────

class ViewsTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('corretor', password='senha123')
        self.staff = User.objects.create_user('admin_test', password='senha123', is_staff=True)

    def _make(self, usuario=None, cliente='Teste'):
        return Simulation.objects.create(
            usuario=usuario or self.user, cliente=cliente,
            valor_imovel=200000, entrada=40000,
            taxa_juros='0.75', prazo_meses=240, sistema='SAC',
        )

    # Redirecionamentos sem login
    def test_simular_redireciona_sem_login(self):
        self.assertEqual(self.client.get(reverse('simulador:simular')).status_code, 302)

    def test_dashboard_redireciona_sem_login(self):
        self.assertEqual(self.client.get(reverse('simulador:dashboard')).status_code, 302)

    def test_historico_redireciona_sem_login(self):
        self.assertEqual(self.client.get(reverse('simulador:historico')).status_code, 302)

    def test_oraculo_redireciona_sem_login(self):
        self.assertEqual(self.client.get(reverse('simulador:oraculo')).status_code, 302)

    # Simular
    def test_simular_get(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('simulador:simular')).status_code, 200)

    def test_simular_post_cria_registro(self):
        self.client.force_login(self.user)
        self.client.post(reverse('simulador:simular'), {
            'cliente': 'Fulano', 'valor_imovel': '300000', 'entrada': '60000',
            'taxa_juros': '0.75', 'meses': '360', 'sistema': 'SAC',
        })
        self.assertEqual(Simulation.objects.count(), 1)

    def test_simular_associa_usuario(self):
        self.client.force_login(self.user)
        self.client.post(reverse('simulador:simular'), {
            'cliente': 'Beltrano', 'valor_imovel': '250000', 'entrada': '50000',
            'taxa_juros': '0.75', 'meses': '240', 'sistema': 'PRICE',
        })
        self.assertEqual(Simulation.objects.first().usuario, self.user)

    def test_simular_cliente_vazio_nao_salva(self):
        self.client.force_login(self.user)
        self.client.post(reverse('simulador:simular'), {
            'cliente': '', 'valor_imovel': '300000', 'entrada': '60000',
            'taxa_juros': '0.75', 'meses': '360', 'sistema': 'SAC',
        })
        self.assertEqual(Simulation.objects.count(), 0)

    def test_simular_entrada_maior_que_imovel_nao_salva(self):
        self.client.force_login(self.user)
        self.client.post(reverse('simulador:simular'), {
            'cliente': 'X', 'valor_imovel': '100000', 'entrada': '200000',
            'taxa_juros': '0.75', 'meses': '120', 'sistema': 'SAC',
        })
        self.assertEqual(Simulation.objects.count(), 0)

    # Histórico — isolamento
    def test_usuario_ve_apenas_proprias_sims(self):
        outro = User.objects.create_user('outro', password='senha')
        sim_outro = self._make(usuario=outro, cliente='Outro')
        sim_proprio = self._make(usuario=self.user, cliente='Próprio')
        self.client.force_login(self.user)
        ids = [s.pk for s in self.client.get(reverse('simulador:historico')).context['simulacoes']]
        self.assertIn(sim_proprio.pk, ids)
        self.assertNotIn(sim_outro.pk, ids)

    def test_staff_ve_todas_as_sims(self):
        outro = User.objects.create_user('outro2', password='senha')
        sim = self._make(usuario=outro)
        self.client.force_login(self.staff)
        ids = [s.pk for s in self.client.get(reverse('simulador:historico')).context['simulacoes']]
        self.assertIn(sim.pk, ids)

    def test_historico_filtro_busca(self):
        self._make(cliente='Ana Lima')
        self._make(cliente='Bruno Costa')
        self.client.force_login(self.user)
        resp = self.client.get(reverse('simulador:historico') + '?busca=Ana')
        clientes = [s.cliente for s in resp.context['simulacoes']]
        self.assertTrue(all('Ana' in c for c in clientes))

    # Excluir
    def test_excluir_propria(self):
        sim = self._make()
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('simulador:excluir_simulacao', args=[sim.pk])).status_code, 302)
        self.assertFalse(Simulation.objects.filter(pk=sim.pk).exists())

    def test_excluir_de_outro_retorna_404(self):
        outro = User.objects.create_user('outro3', password='senha')
        sim = self._make(usuario=outro)
        self.client.force_login(self.user)
        self.assertEqual(self.client.post(reverse('simulador:excluir_simulacao', args=[sim.pk])).status_code, 404)
        self.assertTrue(Simulation.objects.filter(pk=sim.pk).exists())

    # Alterar status
    def test_alterar_status_valido(self):
        sim = self._make()
        self.client.force_login(self.user)
        self.client.post(reverse('simulador:alterar_status', args=[sim.pk]), {'status': 'aprovado'})
        sim.refresh_from_db()
        self.assertEqual(sim.status, 'aprovado')

    def test_alterar_status_invalido_nao_muda(self):
        sim = self._make()
        self.client.force_login(self.user)
        self.client.post(reverse('simulador:alterar_status', args=[sim.pk]), {'status': 'xyz'})
        sim.refresh_from_db()
        self.assertEqual(sim.status, 'novo')

    # Oráculo
    def test_oraculo_get(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('simulador:oraculo'))
        self.assertEqual(resp.status_code, 200)
        self.assertIsNone(resp.context['resultado'])

    def test_oraculo_post_retorna_resultado(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('simulador:oraculo'), {
            'renda': '10000', 'entrada': '50000',
            'prazo_anos': '30', 'taxa_anual': '9.99', 'comprometimento': '30',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context['resultado'])
        self.assertIn('poder_compra', resp.context['resultado'])

    # Gestão de usuários
    def test_usuarios_lista_bloqueada_para_corretor(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('simulador:usuarios_lista')).status_code, 302)

    def test_usuarios_lista_acessivel_por_staff(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('simulador:usuarios_lista')).status_code, 200)

    def test_usuario_criar_post_valido(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('simulador:usuario_criar'), {
            'username': 'novo_corretor', 'first_name': 'Novo', 'last_name': 'Corretor',
            'email': 'novo@teste.com', 'password1': 'senha456', 'password2': 'senha456',
        })
        self.assertTrue(User.objects.filter(username='novo_corretor').exists())

    def test_usuario_criar_senha_curta_nao_cria(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('simulador:usuario_criar'), {
            'username': 'invalido', 'password1': 'abc', 'password2': 'abc',
        })
        self.assertFalse(User.objects.filter(username='invalido').exists())

    def test_usuario_toggle_desativa(self):
        alvo = User.objects.create_user('alvo', password='senha', is_active=True)
        self.client.force_login(self.staff)
        self.client.post(reverse('simulador:usuario_toggle_ativo', args=[alvo.pk]))
        alvo.refresh_from_db()
        self.assertFalse(alvo.is_active)

    def test_usuario_nao_pode_desativar_a_si_mesmo(self):
        self.client.force_login(self.staff)
        self.client.post(reverse('simulador:usuario_toggle_ativo', args=[self.staff.pk]))
        self.staff.refresh_from_db()
        self.assertTrue(self.staff.is_active)
