from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count
from django.core.paginator import Paginator
from django.http import HttpResponse
from .models import Simulation
from .calculos import calcular_sac, calcular_price
from collections import defaultdict
from functools import wraps
from io import BytesIO
import json
import datetime


def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.conf import settings
            return redirect(settings.LOGIN_URL)
        if not request.user.is_staff:
            messages.error(request, 'Acesso restrito a administradores.')
            return redirect('simulador:simular')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@require_http_methods(["GET", "POST"])
def simular(request):
    resultado = None

    if request.method == "POST":
        try:
            valor_imovel = float(request.POST.get("valor_imovel", 0))
            valor_entrada = float(request.POST.get("entrada", 0))
            taxa_juros = float(request.POST.get("taxa_juros", 0))
            prazo_meses = int(request.POST.get("meses", 0))
            sistema = request.POST.get("sistema", "SAC").upper()
            cliente = request.POST.get("cliente", "").strip()
            observacoes = request.POST.get("observacoes", "").strip()

            if valor_entrada >= valor_imovel:
                raise ValueError("A entrada não pode ser maior ou igual ao valor do imóvel.")
            if taxa_juros <= 0 or prazo_meses <= 0:
                raise ValueError("Taxa de juros e prazo devem ser maiores que zero.")
            if not cliente:
                raise ValueError("O nome do cliente é obrigatório.")

            valor_financiado = valor_imovel - valor_entrada

            if sistema == "SAC":
                parcelas = calcular_sac(valor_financiado, taxa_juros, prazo_meses)
            else:
                parcelas = calcular_price(valor_financiado, taxa_juros, prazo_meses)

            Simulation.objects.create(
                usuario=request.user,
                cliente=cliente,
                valor_imovel=valor_imovel,
                entrada=valor_entrada,
                taxa_juros=taxa_juros,
                prazo_meses=prazo_meses,
                sistema=sistema,
                observacoes=observacoes,
            )

            total_pago = sum(float(p["valor"]) for p in parcelas) if parcelas else 0
            primeira_parcela = parcelas[0]["valor"] if parcelas else "0.00"
            ultima_parcela = parcelas[-1]["valor"] if parcelas else "0.00"

            resultado = {
                "sistema": sistema,
                "valor_imovel": f"{valor_imovel:.2f}",
                "entrada": f"{valor_entrada:.2f}",
                "valor_financiado": f"{valor_financiado:.2f}",
                "taxa_juros": f"{taxa_juros:.2f}",
                "meses": prazo_meses,
                "primeira_parcela": primeira_parcela,
                "ultima_parcela": ultima_parcela,
                "total_pago": f"{total_pago:.2f}",
                "parcelas": parcelas,
                "cliente": cliente,
            }

        except (ValueError, TypeError) as e:
            messages.error(request, f"Erro nos dados informados: {e}")
        except Exception as e:
            messages.error(request, f"Ocorreu um erro inesperado: {e}")

    return render(request, "simulador/index.html", {"resultado": resultado})


@login_required
def dashboard(request):
    # Admin vê tudo, outros usuários veem apenas suas próprias simulações
    if request.user.is_staff:
        qs = Simulation.objects.all()
    else:
        qs = Simulation.objects.filter(usuario=request.user)

    total = qs.count()
    volume = qs.aggregate(total=Sum('valor_imovel'))['total'] or 0
    ticket_medio = (volume / total) if total > 0 else 0

    # Gráfico de timeline: simulações por dia
    por_dia = defaultdict(int)
    for sim in qs.values('criado_em'):
        dia = sim['criado_em'].date().strftime('%d/%m/%Y')
        por_dia[dia] += 1

    dias_ordenados = sorted(por_dia.keys(), key=lambda d: d.split('/')[::-1])
    timeline_labels = dias_ordenados
    timeline_data = [por_dia[d] for d in dias_ordenados]

    # Gráfico de pizza: distribuição por status
    status_qs = qs.values('status').annotate(total=Count('status'))
    status_map = {s: label for s, label in Simulation.STATUS_CHOICES}
    status_labels = [status_map.get(s['status'], s['status']) for s in status_qs]
    status_data = [s['total'] for s in status_qs]

    context = {
        'total': total,
        'volume': volume,
        'ticket_medio': ticket_medio,
        'timeline_labels': json.dumps(timeline_labels),
        'timeline_data': json.dumps(timeline_data),
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
    }
    return render(request, 'simulador/dashboard.html', context)


@login_required
def historico(request):
    if request.user.is_staff:
        qs = Simulation.objects.select_related('usuario').all()
    else:
        qs = Simulation.objects.filter(usuario=request.user)

    # Filtros
    busca = request.GET.get('busca', '').strip()
    filtro_status = request.GET.get('status', '')
    filtro_sistema = request.GET.get('sistema', '')

    if busca:
        qs = qs.filter(cliente__icontains=busca)
    if filtro_status:
        qs = qs.filter(status=filtro_status)
    if filtro_sistema:
        qs = qs.filter(sistema=filtro_sistema)

    # Paginação
    paginator = Paginator(qs, 10)
    page = request.GET.get('page', 1)
    simulacoes = paginator.get_page(page)

    context = {
        'simulacoes': simulacoes,
        'busca': busca,
        'filtro_status': filtro_status,
        'filtro_sistema': filtro_sistema,
        'status_choices': Simulation.STATUS_CHOICES,
        'sistema_choices': Simulation.SISTEMA_CHOICES,
        'total_filtrado': qs.count(),
    }
    return render(request, 'simulador/historico.html', context)


@login_required
@require_POST
def excluir_simulacao(request, pk):
    if request.user.is_staff:
        sim = get_object_or_404(Simulation, pk=pk)
    else:
        sim = get_object_or_404(Simulation, pk=pk, usuario=request.user)

    cliente = sim.cliente
    sim.delete()
    messages.success(request, f'Simulação de "{cliente}" excluída com sucesso.')
    return redirect('simulador:historico')


@login_required
@require_POST
def alterar_status(request, pk):
    if request.user.is_staff:
        sim = get_object_or_404(Simulation, pk=pk)
    else:
        sim = get_object_or_404(Simulation, pk=pk, usuario=request.user)

    novo_status = request.POST.get('status', '')
    status_validos = [s for s, _ in Simulation.STATUS_CHOICES]
    if novo_status in status_validos:
        sim.status = novo_status
        sim.save(update_fields=['status'])
        messages.success(request, f'Status de "{sim.cliente}" atualizado para "{sim.get_status_display()}".')
    else:
        messages.error(request, 'Status inválido.')

    return redirect('simulador:historico')


@login_required
def oraculo(request):
    resultado = None

    if request.method == 'POST':
        try:
            renda = float(request.POST.get('renda', 0))
            entrada = float(request.POST.get('entrada', 0))
            prazo_anos = int(request.POST.get('prazo_anos', 30))
            taxa_anual = float(request.POST.get('taxa_anual', 9.99))
            comprometimento = float(request.POST.get('comprometimento', 30))

            if renda <= 0:
                raise ValueError("A renda mensal deve ser maior que zero.")

            # Cálculo reverso: PMT -> PV (Price)
            margem_parcela = renda * (comprometimento / 100)
            taxa_mensal = (taxa_anual / 100) / 12
            meses = prazo_anos * 12
            valor_financiavel = margem_parcela * ((1 - (1 + taxa_mensal) ** (-meses)) / taxa_mensal)
            poder_compra = valor_financiavel + entrada

            resultado = {
                'poder_compra': f'{poder_compra:,.2f}',
                'valor_financiavel': f'{valor_financiavel:,.2f}',
                'margem_parcela': f'{margem_parcela:,.2f}',
                'renda': f'{renda:,.2f}',
                'entrada': f'{entrada:,.2f}',
                'prazo_anos': prazo_anos,
                'taxa_anual': taxa_anual,
                'comprometimento': comprometimento,
                'interpretacao': (
                    f'Com renda de R$ {renda:,.2f}, o banco libera uma parcela de até '
                    f'R$ {margem_parcela:,.2f} ({comprometimento:.0f}% da renda). '
                    f'Isso financia até R$ {valor_financiavel:,.2f} em {prazo_anos} anos, '
                    f'dando um poder de compra de R$ {poder_compra:,.2f}.'
                ),
            }
        except (ValueError, TypeError) as e:
            messages.error(request, f'Erro nos dados informados: {e}')
        except Exception as e:
            messages.error(request, f'Ocorreu um erro inesperado: {e}')

    return render(request, 'simulador/oraculo.html', {'resultado': resultado})


@login_required
@require_http_methods(["GET", "POST"])
def comparativo(request):
    resultado = None

    if request.method == 'POST':
        try:
            valor_imovel = float(request.POST.get('valor_imovel', 0))
            valor_entrada = float(request.POST.get('entrada', 0))
            taxa_juros = float(request.POST.get('taxa_juros', 0))
            prazo_meses = int(request.POST.get('meses', 0))

            if valor_entrada >= valor_imovel:
                raise ValueError("A entrada não pode ser maior ou igual ao valor do imóvel.")
            if taxa_juros <= 0 or prazo_meses <= 0:
                raise ValueError("Taxa de juros e prazo devem ser maiores que zero.")

            valor_financiado = valor_imovel - valor_entrada
            parcelas_sac = calcular_sac(valor_financiado, taxa_juros, prazo_meses)
            parcelas_price = calcular_price(valor_financiado, taxa_juros, prazo_meses)

            def resumo(parcelas):
                total = sum(float(p['valor']) for p in parcelas)
                return {
                    'primeira': parcelas[0]['valor'],
                    'ultima': parcelas[-1]['valor'],
                    'total_pago': f'{total:,.2f}',
                    'total_juros': f'{total - valor_financiado:,.2f}',
                }

            # Amostragem do saldo devedor para o gráfico (máx 60 pontos)
            passo = max(1, prazo_meses // 60)
            indices = list(range(0, prazo_meses, passo))
            if (prazo_meses - 1) not in indices:
                indices.append(prazo_meses - 1)

            labels = [parcelas_sac[i]['numero'] for i in indices]
            saldo_sac = [float(parcelas_sac[i]['saldo_devedor']) for i in indices]
            saldo_price = [float(parcelas_price[i]['saldo_devedor']) for i in indices]

            resultado = {
                'sac': resumo(parcelas_sac),
                'price': resumo(parcelas_price),
                'valor_financiado': f'{valor_financiado:,.2f}',
                'labels': json.dumps(labels),
                'saldo_sac': json.dumps(saldo_sac),
                'saldo_price': json.dumps(saldo_price),
            }
        except (ValueError, TypeError) as e:
            messages.error(request, f'Erro nos dados informados: {e}')

    return render(request, 'simulador/comparativo.html', {'resultado': resultado})


@login_required
@require_http_methods(["GET", "POST"])
def perfil(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        errors = []
        if password1:
            if password1 != password2:
                errors.append('As senhas não conferem.')
            elif len(password1) < 6:
                errors.append('A senha deve ter no mínimo 6 caracteres.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.email = email
            if password1:
                request.user.set_password(password1)
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, request.user)
            request.user.save()
            messages.success(request, 'Perfil atualizado com sucesso.')
            return redirect('simulador:perfil')

    return render(request, 'simulador/perfil.html', {
        'form_data': {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
    })


@login_required
def exportar_pdf(request, pk):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT

    if request.user.is_staff:
        sim = get_object_or_404(Simulation, pk=pk)
    else:
        sim = get_object_or_404(Simulation, pk=pk, usuario=request.user)

    parcelas = (calcular_sac if sim.sistema == 'SAC' else calcular_price)(
        float(sim.valor_financiado), float(sim.taxa_juros), sim.prazo_meses
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)

    styles = getSampleStyleSheet()
    azul = colors.HexColor('#1a3c5e')
    azul_claro = colors.HexColor('#2e86c1')
    cinza = colors.HexColor('#f0f4f8')

    titulo_style = ParagraphStyle('titulo', parent=styles['Title'],
                                   textColor=azul, fontSize=18, spaceAfter=4)
    sub_style = ParagraphStyle('sub', parent=styles['Normal'],
                                textColor=azul_claro, fontSize=10, spaceAfter=12)
    label_style = ParagraphStyle('label', parent=styles['Normal'],
                                  textColor=colors.grey, fontSize=8)

    total_pago = sum(float(p['valor']) for p in parcelas)
    total_juros = total_pago - float(sim.valor_financiado)

    story = [
        Paragraph('Proposta de Financiamento', titulo_style),
        Paragraph(f'Emitido em {datetime.date.today().strftime("%d/%m/%Y")} — Sistema {sim.sistema}', sub_style),
        Spacer(1, 0.3*cm),
    ]

    # Dados resumo
    resumo = [
        ['Cliente', sim.cliente, 'Usuário', sim.usuario.get_full_name() or sim.usuario.username],
        ['Valor do Imóvel', f'R$ {float(sim.valor_imovel):,.2f}', 'Entrada', f'R$ {float(sim.entrada):,.2f}'],
        ['Valor Financiado', f'R$ {float(sim.valor_financiado):,.2f}', 'Taxa Mensal', f'{float(sim.taxa_juros):.2f}%'],
        ['Prazo', f'{sim.prazo_meses} meses', 'Total Pago', f'R$ {total_pago:,.2f}'],
        ['Total em Juros', f'R$ {total_juros:,.2f}', 'Status', sim.get_status_display()],
    ]
    t_resumo = Table(resumo, colWidths=[3.5*cm, 5.5*cm, 3.5*cm, 5.5*cm])
    t_resumo.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), cinza),
        ('BACKGROUND', (2, 0), (2, -1), cinza),
        ('TEXTCOLOR', (0, 0), (0, -1), azul),
        ('TEXTCOLOR', (2, 0), (2, -1), azul),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
        ('PADDING', (0, 0), (-1, -1), 6),
    ]))
    story += [t_resumo, Spacer(1, 0.5*cm)]

    # Tabela de parcelas (primeiras 24 + últimas 3)
    story.append(Paragraph('Tabela de Parcelas', ParagraphStyle(
        'h2', parent=styles['Heading2'], textColor=azul, fontSize=12, spaceAfter=6)))

    cabecalho = [['#', 'Parcela', 'Amortização', 'Juros', 'Saldo Devedor']]
    exibir = parcelas[:24] + (parcelas[-3:] if len(parcelas) > 27 else [])
    linhas = cabecalho + [
        [p['numero'], f'R$ {p["valor"]}', f'R$ {p["amortizacao"]}',
         f'R$ {p["juros"]}', f'R$ {p["saldo_devedor"]}']
        for p in exibir
    ]
    if len(parcelas) > 27:
        linhas.insert(25, ['...', '...', '...', '...', '...'])

    t_parcelas = Table(linhas, colWidths=[1.2*cm, 3.8*cm, 3.8*cm, 3.8*cm, 4.4*cm])
    t_parcelas.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), azul),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f7ff')]),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#dee2e6')),
        ('PADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_parcelas)

    doc.build(story)
    buffer.seek(0)
    nome = f'proposta_{sim.cliente.replace(" ", "_")}.pdf'
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{nome}"'
    return response


@login_required
def exportar_excel(request, pk):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    if request.user.is_staff:
        sim = get_object_or_404(Simulation, pk=pk)
    else:
        sim = get_object_or_404(Simulation, pk=pk, usuario=request.user)

    parcelas_sac = calcular_sac(float(sim.valor_financiado), float(sim.taxa_juros), sim.prazo_meses)
    parcelas_price = calcular_price(float(sim.valor_financiado), float(sim.taxa_juros), sim.prazo_meses)

    wb = openpyxl.Workbook()
    azul = 'FF1A3C5E'
    azul_claro = 'FF2E86C1'
    cinza = 'FFF0F4F8'

    header_font = Font(name='Calibri', bold=True, color='FFFFFFFF', size=11)
    header_fill = PatternFill('solid', fgColor=azul)
    sub_fill = PatternFill('solid', fgColor=azul_claro)
    center = Alignment(horizontal='center', vertical='center')
    thin = Border(
        left=Side(style='thin', color='FFCFD8DD'),
        right=Side(style='thin', color='FFCFD8DD'),
        top=Side(style='thin', color='FFCFD8DD'),
        bottom=Side(style='thin', color='FFCFD8DD'),
    )

    def estilizar_cabecalho(ws, colunas):
        ws.append(colunas)
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center
            cell.border = thin

    def estilizar_linhas(ws, inicio=2):
        alt_fill = PatternFill('solid', fgColor='FFF0F7FF')
        for i, row in enumerate(ws.iter_rows(min_row=inicio)):
            for cell in row:
                cell.alignment = center
                cell.border = thin
                if i % 2 == 1:
                    cell.fill = alt_fill

    def ajustar_colunas(ws):
        for col in ws.columns:
            max_len = max(len(str(c.value or '')) for c in col) + 4
            ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len, 25)

    # Aba Resumo
    ws_resumo = wb.active
    ws_resumo.title = 'Resumo'
    estilizar_cabecalho(ws_resumo, ['Campo', 'Valor'])
    dados_resumo = [
        ('Cliente', sim.cliente),
        ('Valor do Imóvel', f'R$ {float(sim.valor_imovel):,.2f}'),
        ('Entrada', f'R$ {float(sim.entrada):,.2f}'),
        ('Valor Financiado', f'R$ {float(sim.valor_financiado):,.2f}'),
        ('Taxa de Juros Mensal', f'{float(sim.taxa_juros):.2f}%'),
        ('Prazo', f'{sim.prazo_meses} meses'),
        ('Sistema', sim.sistema),
        ('Status', sim.get_status_display()),
        ('Data da Simulação', sim.criado_em.strftime('%d/%m/%Y %H:%M')),
    ]
    for row in dados_resumo:
        ws_resumo.append(row)
    estilizar_linhas(ws_resumo)
    ajustar_colunas(ws_resumo)

    # Aba SAC
    ws_sac = wb.create_sheet('Tabela SAC')
    estilizar_cabecalho(ws_sac, ['#', 'Parcela (R$)', 'Amortização (R$)', 'Juros (R$)', 'Saldo Devedor (R$)'])
    for p in parcelas_sac:
        ws_sac.append([p['numero'], p['valor'], p['amortizacao'], p['juros'], p['saldo_devedor']])
    estilizar_linhas(ws_sac)
    ajustar_colunas(ws_sac)

    # Aba PRICE
    ws_price = wb.create_sheet('Tabela PRICE')
    estilizar_cabecalho(ws_price, ['#', 'Parcela (R$)', 'Amortização (R$)', 'Juros (R$)', 'Saldo Devedor (R$)'])
    for p in parcelas_price:
        ws_price.append([p['numero'], p['valor'], p['amortizacao'], p['juros'], p['saldo_devedor']])
    estilizar_linhas(ws_price)
    ajustar_colunas(ws_price)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    nome = f'comparativo_{sim.cliente.replace(" ", "_")}.xlsx'
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{nome}"'
    return response


@login_required
def exportar_historico(request):
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter

    if request.user.is_staff:
        qs = Simulation.objects.select_related('usuario').all()
    else:
        qs = Simulation.objects.filter(usuario=request.user)

    busca = request.GET.get('busca', '').strip()
    filtro_status = request.GET.get('status', '')
    filtro_sistema = request.GET.get('sistema', '')

    if busca:
        qs = qs.filter(cliente__icontains=busca)
    if filtro_status:
        qs = qs.filter(status=filtro_status)
    if filtro_sistema:
        qs = qs.filter(sistema=filtro_sistema)

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = 'Histórico'

    azul = 'FF1A3C5E'
    header_font = Font(name='Calibri', bold=True, color='FFFFFFFF', size=11)
    header_fill = PatternFill('solid', fgColor=azul)
    center = Alignment(horizontal='center', vertical='center')
    thin = Border(
        left=Side(style='thin', color='FFCFD8DD'),
        right=Side(style='thin', color='FFCFD8DD'),
        top=Side(style='thin', color='FFCFD8DD'),
        bottom=Side(style='thin', color='FFCFD8DD'),
    )

    colunas = ['#', 'Cliente']
    if request.user.is_staff:
        colunas.append('Usuário')
    colunas += ['Valor Imóvel (R$)', 'Entrada (R$)', 'Valor Financiado (R$)',
                'Taxa Mensal (%)', 'Prazo (meses)', 'Sistema', 'Status', 'Data']

    ws.append(colunas)
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = thin

    alt_fill = PatternFill('solid', fgColor='FFF0F7FF')
    status_map = dict(Simulation.STATUS_CHOICES)

    for i, sim in enumerate(qs.order_by('-criado_em'), start=1):
        row = [sim.pk, sim.cliente]
        if request.user.is_staff:
            row.append(sim.usuario.username)
        row += [
            float(sim.valor_imovel),
            float(sim.entrada),
            float(sim.valor_financiado),
            float(sim.taxa_juros),
            sim.prazo_meses,
            sim.sistema,
            status_map.get(sim.status, sim.status),
            sim.criado_em.strftime('%d/%m/%Y %H:%M'),
        ]
        ws.append(row)
        for cell in ws[i + 1]:
            cell.alignment = center
            cell.border = thin
            if i % 2 == 0:
                cell.fill = alt_fill

    for col in ws.columns:
        max_len = max(len(str(c.value or '')) for c in col) + 4
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max_len, 30)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filtros = '_'.join(filter(None, [busca, filtro_status, filtro_sistema])) or 'completo'
    nome = f'historico_{filtros}_{datetime.date.today().strftime("%Y%m%d")}.xlsx'
    response = HttpResponse(
        buffer,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{nome}"'
    return response


@login_required
def detalhe_simulacao(request, pk):
    if request.user.is_staff:
        sim = get_object_or_404(Simulation, pk=pk)
    else:
        sim = get_object_or_404(Simulation, pk=pk, usuario=request.user)

    fn = calcular_sac if sim.sistema == 'SAC' else calcular_price
    parcelas = fn(float(sim.valor_financiado), float(sim.taxa_juros), sim.prazo_meses)
    total_pago = sum(float(p['valor']) for p in parcelas)
    total_juros = total_pago - float(sim.valor_financiado)

    return render(request, 'simulador/detalhe.html', {
        'sim': sim,
        'parcelas': parcelas,
        'total_pago': total_pago,
        'total_juros': total_juros,
        'primeira_parcela': parcelas[0]['valor'] if parcelas else '0.00',
        'ultima_parcela': parcelas[-1]['valor'] if parcelas else '0.00',
    })


# ── Gestão de Usuários (staff only) ──────────────────────────────────────────

@staff_required
def usuarios_lista(request):
    usuarios = User.objects.all().order_by('username').annotate(
        total_sims=Count('simulacoes')
    )
    return render(request, 'simulador/usuarios_lista.html', {'usuarios': usuarios})


@staff_required
@require_http_methods(["GET", "POST"])
def usuario_criar(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        is_staff = request.POST.get('is_staff') == 'on'

        errors = []
        if not username:
            errors.append('O nome de usuário é obrigatório.')
        elif User.objects.filter(username=username).exists():
            errors.append(f'O usuário "{username}" já existe.')
        if not password1:
            errors.append('A senha é obrigatória.')
        elif password1 != password2:
            errors.append('As senhas não conferem.')
        elif len(password1) < 6:
            errors.append('A senha deve ter no mínimo 6 caracteres.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            User.objects.create_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                password=password1,
                is_staff=is_staff,
            )
            messages.success(request, f'Usuário "{username}" criado com sucesso.')
            return redirect('simulador:usuarios_lista')

    form_data = {'first_name': request.POST.get('first_name', ''), 'last_name': request.POST.get('last_name', ''), 'email': request.POST.get('email', ''), 'is_staff': request.POST.get('is_staff') == 'on'}
    return render(request, 'simulador/usuario_form.html', {'modo': 'criar', 'usuario': None, 'form_data': form_data})


@staff_required
@require_http_methods(["GET", "POST"])
def usuario_editar(request, pk):
    usuario = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        is_staff = request.POST.get('is_staff') == 'on'
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')

        errors = []
        if password1:
            if password1 != password2:
                errors.append('As senhas não conferem.')
            elif len(password1) < 6:
                errors.append('A senha deve ter no mínimo 6 caracteres.')

        if errors:
            for e in errors:
                messages.error(request, e)
        else:
            usuario.first_name = first_name
            usuario.last_name = last_name
            usuario.email = email
            if usuario.pk != request.user.pk:
                usuario.is_staff = is_staff
            if password1:
                usuario.set_password(password1)
            usuario.save()
            messages.success(request, f'Usuário "{usuario.username}" atualizado com sucesso.')
            return redirect('simulador:usuarios_lista')

    form_data = {'first_name': request.POST.get('first_name', usuario.first_name), 'last_name': request.POST.get('last_name', usuario.last_name), 'email': request.POST.get('email', usuario.email), 'is_staff': (request.POST.get('is_staff') == 'on') if request.method == 'POST' else usuario.is_staff}
    return render(request, 'simulador/usuario_form.html', {'modo': 'editar', 'usuario': usuario, 'form_data': form_data})


@staff_required
@require_POST
def usuario_toggle_ativo(request, pk):
    usuario = get_object_or_404(User, pk=pk)
    if usuario.pk == request.user.pk:
        messages.error(request, 'Você não pode desativar sua própria conta.')
    else:
        usuario.is_active = not usuario.is_active
        usuario.save(update_fields=['is_active'])
        estado = 'ativado' if usuario.is_active else 'desativado'
        messages.success(request, f'Usuário "{usuario.username}" {estado} com sucesso.')
    return redirect('simulador:usuarios_lista')
