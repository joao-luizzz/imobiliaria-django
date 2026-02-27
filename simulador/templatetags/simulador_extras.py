from django import template

register = template.Library()


@register.filter(name='brl')
def brl(value):
    """Formata número como moeda brasileira: 1.234.567,89"""
    try:
        if isinstance(value, str):
            # Remove separadores de milhar no padrão americano, se houver
            value = value.replace(',', '')
        num = float(value)
        # Formata com separadores e converte para padrão brasileiro
        formatted = f'{num:,.2f}'  # ex: "1,234,567.89"
        return formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return value
