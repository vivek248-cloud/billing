from django import template

register = template.Library()

@register.filter
def indian_currency(value):
    """
    Converts a number to Indian currency format (e.g., ₹44,00,000)
    """
    try:
        value = float(value)
    except:
        return value

    value = int(value)
    s = str(value)[::-1]
    result = s[:3]
    for i in range(3, len(s), 2):
        result += ',' + s[i:i+2]
    return '' + result[::-1]
