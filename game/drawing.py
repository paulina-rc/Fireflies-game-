"""
Funciones de ayuda para colores y dibujos simples.

No importan Kivy: solo cambian atributos de instrucciones de dibujo que
reciben (Ellipse, Triangle), así se pueden usar desde cualquier archivo.
"""


def hex_to_rgb(code):
    """Convierte un color '#RRGGBB' a una tupla (r, g, b) con valores 0..1,
    que es el formato que usa Kivy."""
    code = code.lstrip('#')
    return tuple(int(code[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def mix(color_a, color_b, t):
    """Mezcla dos colores: t=0 da color_a, t=1 da color_b."""
    return tuple(a * (1 - t) + b * t for a, b in zip(color_a, color_b))


def set_circle(ellipse, x, y, radius):
    """Coloca una Ellipse de Kivy como un círculo de centro (x, y)."""
    ellipse.pos = (x - radius, y - radius)
    ellipse.size = (radius * 2, radius * 2)


def place_heart(circle_1, circle_2, triangle, cx, cy, r):
    """Un corazón son dos círculos arriba y un triángulo abajo.
    Los números son las proporciones de la forma del corazón."""
    rc = r * 0.56
    set_circle(circle_1, cx - 0.5 * r, cy + 0.3 * r, rc)
    set_circle(circle_2, cx + 0.5 * r, cy + 0.3 * r, rc)
    triangle.points = [cx - 1.04 * r, cy + 0.18 * r,
                       cx + 1.04 * r, cy + 0.18 * r,
                       cx, cy - 1.0 * r]
