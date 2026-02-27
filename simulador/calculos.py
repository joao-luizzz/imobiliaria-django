def calcular_sac(valor_financiado, taxa_anual, prazo_meses):
    if prazo_meses <= 0: return []
    
    taxa_mensal = (taxa_anual / 100) / 12 if taxa_anual > 0 else 0
    amortizacao = valor_financiado / prazo_meses
    saldo_devedor = valor_financiado
    parcelas = []

    for i in range(1, prazo_meses + 1):
        juros = saldo_devedor * taxa_mensal
        valor_parcela = amortizacao + juros
        saldo_devedor -= amortizacao
        
        parcelas.append({
            "numero": i,
            "valor": f"{valor_parcela:.2f}",
            "amortizacao": f"{amortizacao:.2f}",
            "juros": f"{juros:.2f}",
            "saldo_devedor": f"{abs(saldo_devedor):.2f}"
        })
    return parcelas

def calcular_price(valor_financiado, taxa_anual, prazo_meses):
    if prazo_meses <= 0: return []
    
    taxa_mensal = (taxa_anual / 100) / 12 if taxa_anual > 0 else 0
    saldo_devedor = valor_financiado
    parcelas = []

    if taxa_mensal > 0:
        numerador = taxa_mensal * (1 + taxa_mensal) ** prazo_meses
        denominador = ((1 + taxa_mensal) ** prazo_meses) - 1
        valor_parcela = valor_financiado * (numerador / denominador)
    else:
        valor_parcela = valor_financiado / prazo_meses

    for i in range(1, prazo_meses + 1):
        juros = saldo_devedor * taxa_mensal
        amortizacao = valor_parcela - juros
        saldo_devedor -= amortizacao
        
        parcelas.append({
            "numero": i,
            "valor": f"{valor_parcela:.2f}",
            "amortizacao": f"{amortizacao:.2f}",
            "juros": f"{juros:.2f}",
            "saldo_devedor": f"{abs(saldo_devedor):.2f}"
        })
    return parcelas