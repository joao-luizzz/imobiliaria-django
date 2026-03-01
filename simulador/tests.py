import json
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


class ViewsNovosTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user('corretor2', password='senha123')
        self.staff = User.objects.create_user('admin2', password='senha123', is_staff=True)

    # FGTS
    def test_fgts_get(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('simulador:fgts')).status_code, 200)

    def test_fgts_post_modalidade_parcela(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('simulador:fgts'), {
            'valor_financiado': '200000', 'taxa_juros': '0.75',
            'meses': '240', 'sistema': 'SAC',
            'saldo_fgts': '30000', 'modalidade': 'parcela',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context['resultado'])

    def test_fgts_post_modalidade_prazo(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('simulador:fgts'), {
            'valor_financiado': '200000', 'taxa_juros': '0.75',
            'meses': '240', 'sistema': 'PRICE',
            'saldo_fgts': '30000', 'modalidade': 'prazo',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context['resultado'])

    # ITBI
    def test_itbi_get(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('simulador:itbi')).status_code, 200)

    def test_itbi_post(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('simulador:itbi'), {
            'valor_imovel': '300000', 'aliquota_itbi': '2.0',
            'cartorio_percent': '1.0', 'avaliacao': '3000', 'certidoes': '500',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context['resultado'])
        self.assertIn('total_taxas', resp.context['resultado'])

    # IPCA/TR
    def test_ipca_tr_get(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('simulador:ipca_tr')).status_code, 200)

    def test_ipca_tr_post_sac(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('simulador:ipca_tr'), {
            'valor_financiado': '200000', 'taxa_juros': '0.75',
            'meses': '120', 'sistema': 'SAC', 'taxa_correcao': '0.3',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context['resultado'])

    # CET
    def test_cet_get(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('simulador:cet')).status_code, 200)

    def test_cet_post(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('simulador:cet'), {
            'valor_financiado': '200000', 'taxa_juros': '0.75',
            'meses': '240', 'sistema': 'SAC',
            'tarifa_emissao': '1500', 'tarifa_avaliacao': '3000',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context['resultado'])
        self.assertIn('cet_anual', resp.context['resultado'])

    # Consórcio
    def test_consorcio_get(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('simulador:consorcio')).status_code, 200)

    def test_consorcio_post(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('simulador:consorcio'), {
            'valor_bem': '300000', 'meses': '180',
            'taxa_admin_pct': '18', 'fundo_reserva_pct': '3',
            'taxa_juros_financ': '0.75',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context['resultado'])
        self.assertIn('total_consorcio', resp.context['resultado'])

    # Refinanciamento
    def test_refinanciamento_get(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('simulador:refinanciamento')).status_code, 200)

    def test_refinanciamento_post(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('simulador:refinanciamento'), {
            'saldo_devedor': '150000', 'taxa_atual': '0.85',
            'prazo_restante': '200', 'taxa_nova': '0.70',
            'prazo_novo': '200', 'sistema': 'PRICE',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context['resultado'])
        self.assertIn('economia_mensal', resp.context['resultado'])

    # Relatório PDF (staff only)
    def test_relatorio_pdf_requer_staff(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('simulador:relatorio_pdf')).status_code, 302)

    def test_relatorio_pdf_staff_ok(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('simulador:relatorio_pdf'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp['Content-Type'], 'application/pdf')

    # API REST
    def test_api_simular_post(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse('simulador:api_simular'),
            data=json.dumps({'valor_financiado': 200000, 'taxa_juros': 0.75, 'prazo_meses': 120, 'sistema': 'SAC'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('parcelas', data)
        self.assertEqual(len(data['parcelas']), 120)

    def test_api_oraculo_post(self):
        self.client.force_login(self.user)
        resp = self.client.post(
            reverse('simulador:api_oraculo'),
            data=json.dumps({'renda': 10000, 'entrada': 50000, 'prazo_anos': 30, 'taxa_anual': 9.99}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.content)
        self.assertIn('poder_compra', data)


# ── Features novas ─────────────────────────────────────────────────────────────

class FerramentasAnaliseTest(TestCase):
    """Grupo A: comparativo bancos, MCMV, renda mínima, prazo idade, IPCA+"""

    def setUp(self):
        self.user = User.objects.create_user('corretor3', password='senha123')
        self.client.force_login(self.user)

    # Comparativo de bancos
    def test_comparativo_bancos_get(self):
        self.assertEqual(self.client.get(reverse('simulador:comparativo_bancos')).status_code, 200)

    def test_comparativo_bancos_post(self):
        resp = self.client.post(reverse('simulador:comparativo_bancos'), {
            'valor_financiado': '200000', 'prazo_meses': '240', 'sistema': 'SAC',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertIsNotNone(resp.context['resultado'])
        self.assertIn('bancos', resp.context['resultado'])
        self.assertEqual(len(resp.context['resultado']['bancos']), 5)

    def test_comparativo_bancos_melhor_e_menor_taxa(self):
        resp = self.client.post(reverse('simulador:comparativo_bancos'), {
            'valor_financiado': '300000', 'prazo_meses': '360', 'sistema': 'PRICE',
        })
        resultado = resp.context['resultado']
        self.assertEqual(resultado['melhor']['nome'], resultado['bancos'][0]['nome'])

    # MCMV
    def test_mcmv_get(self):
        self.assertEqual(self.client.get(reverse('simulador:mcmv')).status_code, 200)

    def test_mcmv_faixa1(self):
        resp = self.client.post(reverse('simulador:mcmv'), {
            'renda': '2000', 'valor_imovel': '150000', 'entrada': '20000', 'prazo_anos': '30',
        })
        self.assertEqual(resp.status_code, 200)
        resultado = resp.context['resultado']
        self.assertIn('Faixa 1', resultado['faixa'])
        self.assertGreater(float(resultado['subsidio']), 0)

    def test_mcmv_faixa3_sem_subsidio(self):
        resp = self.client.post(reverse('simulador:mcmv'), {
            'renda': '11000', 'valor_imovel': '400000', 'entrada': '80000', 'prazo_anos': '30',
        })
        resultado = resp.context['resultado']
        self.assertIn('Faixa 3', resultado['faixa'])
        self.assertEqual(float(resultado['subsidio']), 0)

    # Renda mínima
    def test_renda_minima_get(self):
        self.assertEqual(self.client.get(reverse('simulador:renda_minima')).status_code, 200)

    def test_renda_minima_post(self):
        resp = self.client.post(reverse('simulador:renda_minima'), {
            'valor_imovel': '300000', 'entrada': '60000',
            'taxa_juros': '0.75', 'prazo_meses': '360', 'comprometimento': '30',
        })
        self.assertEqual(resp.status_code, 200)
        resultado = resp.context['resultado']
        self.assertIn('renda_minima', resultado)
        self.assertGreater(float(resultado['renda_minima']), 0)
        self.assertEqual(len(resultado['cenarios']), 3)

    # Prazo por idade
    def test_prazo_idade_get(self):
        self.assertEqual(self.client.get(reverse('simulador:prazo_idade')).status_code, 200)

    def test_prazo_idade_sem_limitacao(self):
        resp = self.client.post(reverse('simulador:prazo_idade'), {
            'idade': '30', 'prazo_desejado': '360',
        })
        resultado = resp.context['resultado']
        self.assertFalse(resultado['foi_limitado'])
        self.assertEqual(resultado['prazo_efetivo'], 360)

    def test_prazo_idade_com_limitacao(self):
        resp = self.client.post(reverse('simulador:prazo_idade'), {
            'idade': '55', 'prazo_desejado': '360',
        })
        resultado = resp.context['resultado']
        self.assertTrue(resultado['foi_limitado'])
        # prazo_max = (80*12+6) - (55*12) = 966 - 660 = 306
        self.assertEqual(resultado['prazo_max'], 306)
        self.assertEqual(resultado['prazo_efetivo'], 306)

    # Financiamento IPCA+
    def test_financiamento_ipca_get(self):
        self.assertEqual(self.client.get(reverse('simulador:financiamento_ipca')).status_code, 200)

    def test_financiamento_ipca_post_tres_cenarios(self):
        resp = self.client.post(reverse('simulador:financiamento_ipca'), {
            'valor_financiado': '200000', 'prazo_meses': '240',
            'spread': '3.5', 'ipca_projetado': '4.5',
        })
        self.assertEqual(resp.status_code, 200)
        resultado = resp.context['resultado']
        self.assertIn('base', resultado)
        self.assertIn('otimista', resultado)
        self.assertIn('pessimista', resultado)
        # pessimista deve ter taxa maior que base
        self.assertGreater(resultado['pessimista']['taxa_anual'], resultado['base']['taxa_anual'])
        self.assertGreater(resultado['base']['taxa_anual'], resultado['otimista']['taxa_anual'])

    # Redirecionamento sem login
    def test_ferramentas_redirecionam_sem_login(self):
        self.client.logout()
        urls = [
            'simulador:comparativo_bancos', 'simulador:mcmv',
            'simulador:renda_minima', 'simulador:prazo_idade',
            'simulador:financiamento_ipca',
        ]
        for name in urls:
            with self.subTest(url=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 302)


class ClientesTest(TestCase):
    """Grupo B: CRUD de clientes"""

    def setUp(self):
        from .models import Cliente
        self.user = User.objects.create_user('corretor4', password='senha123')
        self.outro = User.objects.create_user('outro4', password='senha123')
        self.client.force_login(self.user)
        self.Cliente = Cliente

    def _criar_cliente(self, nome='Ana Lima', usuario=None):
        return self.Cliente.objects.create(
            usuario=usuario or self.user,
            nome=nome, email='ana@teste.com', telefone='11999999999',
        )

    def test_lista_get(self):
        self.assertEqual(self.client.get(reverse('simulador:clientes_lista')).status_code, 200)

    def test_lista_exibe_apenas_proprios(self):
        self._criar_cliente('Meu')
        self._criar_cliente('Outro', usuario=self.outro)
        resp = self.client.get(reverse('simulador:clientes_lista'))
        nomes = [c.nome for c in resp.context['page_obj']]
        self.assertIn('Meu', nomes)
        self.assertNotIn('Outro', nomes)

    def test_criar_get(self):
        self.assertEqual(self.client.get(reverse('simulador:cliente_criar')).status_code, 200)

    def test_criar_post_valido(self):
        self.client.post(reverse('simulador:cliente_criar'), {
            'nome': 'João Novo', 'email': 'joao@teste.com',
            'telefone': '11912345678', 'cpf': '', 'renda_mensal': '5000', 'observacoes': '',
        })
        self.assertTrue(self.Cliente.objects.filter(nome='João Novo', usuario=self.user).exists())

    def test_criar_sem_nome_nao_salva(self):
        self.client.post(reverse('simulador:cliente_criar'), {'nome': ''})
        self.assertEqual(self.Cliente.objects.count(), 0)

    def test_editar_post(self):
        c = self._criar_cliente()
        self.client.post(reverse('simulador:cliente_editar', args=[c.pk]), {
            'nome': 'Ana Lima Editada', 'email': 'ana@teste.com',
            'telefone': '11999999999', 'cpf': '', 'renda_mensal': '', 'observacoes': '',
        })
        c.refresh_from_db()
        self.assertEqual(c.nome, 'Ana Lima Editada')

    def test_editar_de_outro_retorna_404(self):
        c = self._criar_cliente(usuario=self.outro)
        resp = self.client.get(reverse('simulador:cliente_editar', args=[c.pk]))
        self.assertEqual(resp.status_code, 404)

    def test_excluir_post(self):
        c = self._criar_cliente()
        self.client.post(reverse('simulador:cliente_excluir', args=[c.pk]))
        self.assertFalse(self.Cliente.objects.filter(pk=c.pk).exists())

    def test_excluir_de_outro_retorna_404(self):
        c = self._criar_cliente(usuario=self.outro)
        self.client.post(reverse('simulador:cliente_excluir', args=[c.pk]))
        self.assertTrue(self.Cliente.objects.filter(pk=c.pk).exists())

    def test_detalhe_get(self):
        c = self._criar_cliente()
        self.assertEqual(self.client.get(reverse('simulador:cliente_detalhe', args=[c.pk])).status_code, 200)

    def test_redireciona_sem_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('simulador:clientes_lista')).status_code, 302)


class PipelineTest(TestCase):
    """Grupo B: Pipeline Kanban"""

    def setUp(self):
        self.user = User.objects.create_user('corretor5', password='senha123')
        self.client.force_login(self.user)

    def _make_sim(self, status='novo'):
        return Simulation.objects.create(
            usuario=self.user, cliente='Pipeline Teste',
            valor_imovel=200000, entrada=40000,
            taxa_juros='0.75', prazo_meses=240, sistema='SAC', status=status,
        )

    def test_pipeline_get(self):
        self.assertEqual(self.client.get(reverse('simulador:pipeline')).status_code, 200)

    def test_pipeline_exibe_colunas(self):
        resp = self.client.get(reverse('simulador:pipeline'))
        self.assertIn('colunas', resp.context)
        self.assertIn('novo', resp.context['colunas'])
        self.assertIn('aprovado', resp.context['colunas'])

    def test_mover_card_valido(self):
        sim = self._make_sim('novo')
        resp = self.client.post(
            reverse('simulador:mover_card', args=[sim.pk]),
            data=json.dumps({'status': 'em_analise'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        sim.refresh_from_db()
        self.assertEqual(sim.status, 'em_analise')

    def test_mover_card_status_invalido(self):
        sim = self._make_sim('novo')
        self.client.post(
            reverse('simulador:mover_card', args=[sim.pk]),
            data=json.dumps({'status': 'invalido_xyz'}),
            content_type='application/json',
        )
        sim.refresh_from_db()
        self.assertEqual(sim.status, 'novo')

    def test_mover_card_de_outro_retorna_404(self):
        outro = User.objects.create_user('outro5', password='senha')
        sim = Simulation.objects.create(
            usuario=outro, cliente='Outro', valor_imovel=100000, entrada=20000,
            taxa_juros='0.75', prazo_meses=120, sistema='SAC',
        )
        resp = self.client.post(
            reverse('simulador:mover_card', args=[sim.pk]),
            data=json.dumps({'status': 'aprovado'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 404)

    def test_pipeline_redireciona_sem_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('simulador:pipeline')).status_code, 302)


class MetasTest(TestCase):
    """Grupo B: Metas do corretor"""

    def setUp(self):
        from .models import MetaCorretor
        self.user = User.objects.create_user('corretor6', password='senha123')
        self.client.force_login(self.user)
        self.MetaCorretor = MetaCorretor

    def test_metas_get(self):
        self.assertEqual(self.client.get(reverse('simulador:metas')).status_code, 200)

    def test_meta_criar_get(self):
        self.assertEqual(self.client.get(reverse('simulador:meta_criar')).status_code, 200)

    def test_meta_criar_post(self):
        self.client.post(reverse('simulador:meta_criar'), {
            'mes': '1', 'ano': '2026',
            'meta_simulacoes': '20', 'meta_valor': '1000000',
        })
        self.assertTrue(self.MetaCorretor.objects.filter(usuario=self.user, mes=1, ano=2026).exists())

    def test_meta_criar_duplicada_nao_cria(self):
        self.MetaCorretor.objects.create(usuario=self.user, mes=3, ano=2026, meta_simulacoes=10)
        self.client.post(reverse('simulador:meta_criar'), {
            'mes': '3', 'ano': '2026', 'meta_simulacoes': '15', 'meta_valor': '0',
        })
        self.assertEqual(self.MetaCorretor.objects.filter(usuario=self.user, mes=3, ano=2026).count(), 1)

    def test_meta_editar_post(self):
        meta = self.MetaCorretor.objects.create(usuario=self.user, mes=4, ano=2026, meta_simulacoes=10)
        self.client.post(reverse('simulador:meta_editar', args=[meta.pk]), {
            'meta_simulacoes': '25', 'meta_valor': '500000',
        })
        meta.refresh_from_db()
        self.assertEqual(meta.meta_simulacoes, 25)

    def test_meta_excluir(self):
        meta = self.MetaCorretor.objects.create(usuario=self.user, mes=5, ano=2026, meta_simulacoes=10)
        self.client.post(reverse('simulador:meta_excluir', args=[meta.pk]))
        self.assertFalse(self.MetaCorretor.objects.filter(pk=meta.pk).exists())

    def test_meta_excluir_de_outro_retorna_404(self):
        outro = User.objects.create_user('outro6', password='senha')
        meta = self.MetaCorretor.objects.create(usuario=outro, mes=6, ano=2026, meta_simulacoes=5)
        self.client.post(reverse('simulador:meta_excluir', args=[meta.pk]))
        self.assertTrue(self.MetaCorretor.objects.filter(pk=meta.pk).exists())

    def test_metas_redireciona_sem_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('simulador:metas')).status_code, 302)


class AdminViewsTest(TestCase):
    """Grupo C: logs de auditoria e relatório por corretor (staff only)"""

    def setUp(self):
        self.user = User.objects.create_user('corretor7', password='senha123')
        self.staff = User.objects.create_user('admin7', password='senha123', is_staff=True)

    def test_logs_requer_staff(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('simulador:logs_auditoria')).status_code, 302)

    def test_logs_staff_ok(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('simulador:logs_auditoria'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('page_obj', resp.context)

    def test_logs_filtro_por_usuario(self):
        from .models import AuditLog
        AuditLog.objects.create(usuario=self.user, acao='Teste')
        AuditLog.objects.create(usuario=self.staff, acao='Outro')
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('simulador:logs_auditoria') + f'?usuario={self.user.username}')
        logs = list(resp.context['page_obj'])
        self.assertTrue(all(l.usuario == self.user for l in logs))

    def test_relatorio_corretores_requer_staff(self):
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse('simulador:relatorio_corretores')).status_code, 302)

    def test_relatorio_corretores_staff_ok(self):
        self.client.force_login(self.staff)
        resp = self.client.get(reverse('simulador:relatorio_corretores'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('usuarios', resp.context)

    def test_audit_log_criado_ao_simular(self):
        from .models import AuditLog
        self.client.force_login(self.user)
        self.client.post(reverse('simulador:simular'), {
            'cliente': 'AuditTeste', 'valor_imovel': '300000', 'entrada': '60000',
            'taxa_juros': '0.75', 'meses': '360', 'sistema': 'SAC',
        })
        self.assertTrue(AuditLog.objects.filter(usuario=self.user, acao='Criou simulação').exists())


class TwoFATest(TestCase):
    """Grupo D: setup 2FA e verificação com brute-force protection"""

    def setUp(self):
        from .models import UserProfile
        self.user = User.objects.create_user('corretor8', password='senha123')
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.client.force_login(self.user)

    def test_setup_2fa_get(self):
        resp = self.client.get(reverse('simulador:setup_2fa'))
        self.assertEqual(resp.status_code, 200)
        self.assertIn('secret', resp.context)

    def test_ativar_2fa_codigo_valido(self):
        import pyotp
        resp = self.client.get(reverse('simulador:setup_2fa'))
        secret = self.client.session.get('_2fa_setup_secret')
        self.assertIsNotNone(secret)
        codigo = pyotp.TOTP(secret).now()
        resp = self.client.post(reverse('simulador:setup_2fa'), {
            'acao': 'ativar', 'codigo': codigo,
        })
        self.profile.refresh_from_db()
        self.assertTrue(self.profile.totp_enabled)

    def test_ativar_2fa_codigo_invalido(self):
        self.client.get(reverse('simulador:setup_2fa'))
        self.client.post(reverse('simulador:setup_2fa'), {
            'acao': 'ativar', 'codigo': '000000',
        })
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.totp_enabled)

    def test_desativar_2fa(self):
        import pyotp
        secret = pyotp.random_base32()
        self.profile.totp_secret = secret
        self.profile.totp_enabled = True
        self.profile.save()
        session = self.client.session
        session['_2fa_done'] = True
        session.save()
        self.client.post(reverse('simulador:setup_2fa'), {'acao': 'desativar'})
        self.profile.refresh_from_db()
        self.assertFalse(self.profile.totp_enabled)

    def test_verificar_2fa_codigo_correto(self):
        import pyotp
        secret = pyotp.random_base32()
        self.profile.totp_secret = secret
        self.profile.totp_enabled = True
        self.profile.save()
        codigo = pyotp.TOTP(secret).now()
        resp = self.client.post(reverse('simulador:verificar_2fa'), {'codigo': codigo})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(self.client.session.get('_2fa_done'))

    def test_verificar_2fa_codigo_incorreto(self):
        import pyotp
        secret = pyotp.random_base32()
        self.profile.totp_secret = secret
        self.profile.totp_enabled = True
        self.profile.save()
        self.client.post(reverse('simulador:verificar_2fa'), {'codigo': '000000'})
        self.assertFalse(self.client.session.get('_2fa_done', False))

    def test_verificar_2fa_lockout_apos_5_tentativas(self):
        import pyotp
        secret = pyotp.random_base32()
        self.profile.totp_secret = secret
        self.profile.totp_enabled = True
        self.profile.save()
        for _ in range(5):
            self.client.post(reverse('simulador:verificar_2fa'), {'codigo': '000000'})
        # Na 6ª tentativa mesmo com código correto deve estar bloqueado
        session = self.client.session
        self.assertIn('_2fa_lockout_until', session)

    def test_setup_2fa_requer_login(self):
        self.client.logout()
        self.assertEqual(self.client.get(reverse('simulador:setup_2fa')).status_code, 302)
