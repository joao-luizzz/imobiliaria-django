def calcular_sac(valor_financiado, taxa_anual, prazo_meses, mip_mensal=0.0, dfi_mensal=0.0, valor_imovel=None):
    if prazo_meses <= 0: return []
    if valor_imovel is None:
        valor_imovel = valor_financiado

    taxa_mensal = (taxa_anual / 100) / 12 if taxa_anual > 0 else 0
    amortizacao = valor_financiado / prazo_meses
    saldo_devedor = valor_financiado
    parcelas = []

    for i in range(1, prazo_meses + 1):
        juros = saldo_devedor * taxa_mensal
        seguro = round(saldo_devedor * (mip_mensal / 100) + valor_imovel * (dfi_mensal / 100), 2)
        valor_parcela = amortizacao + juros + seguro
        saldo_devedor -= amortizacao

        parcelas.append({
            "numero": i,
            "valor": f"{valor_parcela:.2f}",
            "amortizacao": f"{amortizacao:.2f}",
            "juros": f"{juros:.2f}",
            "seguro": f"{seguro:.2f}",
            "saldo_devedor": f"{abs(saldo_devedor):.2f}"
        })
    return parcelas

def calcular_price(valor_financiado, taxa_anual, prazo_meses, mip_mensal=0.0, dfi_mensal=0.0, valor_imovel=None):
    if prazo_meses <= 0: return []
    if valor_imovel is None:
        valor_imovel = valor_financiado

    taxa_mensal = (taxa_anual / 100) / 12 if taxa_anual > 0 else 0
    saldo_devedor = valor_financiado
    parcelas = []

    if taxa_mensal > 0:
        numerador = taxa_mensal * (1 + taxa_mensal) ** prazo_meses
        denominador = ((1 + taxa_mensal) ** prazo_meses) - 1
        parcela_base = valor_financiado * (numerador / denominador)
    else:
        parcela_base = valor_financiado / prazo_meses

    for i in range(1, prazo_meses + 1):
        juros = saldo_devedor * taxa_mensal
        amortizacao = parcela_base - juros
        seguro = round(saldo_devedor * (mip_mensal / 100) + valor_imovel * (dfi_mensal / 100), 2)
        saldo_devedor -= amortizacao

        parcelas.append({
            "numero": i,
            "valor": f"{parcela_base + seguro:.2f}",
            "amortizacao": f"{amortizacao:.2f}",
            "juros": f"{juros:.2f}",
            "seguro": f"{seguro:.2f}",
            "saldo_devedor": f"{abs(saldo_devedor):.2f}"
        })
    return parcelas
