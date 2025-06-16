from django import template

register = template.Library()

@register.filter
def indian_currency(value):
    """
    Converts a float to Indian currency format (e.g., ₹44,00,000.50)
    """
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value

    # Split integer and decimal parts
    integer_part = int(value)
    decimal_part = f"{value:.2f}".split(".")[1]

    s = str(integer_part)[::-1]
    groups = [s[:3]]
    s = s[3:]

    while s:
        groups.append(s[:2])
        s = s[2:]

    formatted = ",".join(groups)[::-1]
    return f"₹{formatted}.{decimal_part}"

