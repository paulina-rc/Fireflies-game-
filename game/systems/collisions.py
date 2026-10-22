"""
Colisiones por distancia.

Todos los elementos del juego se tratan como círculos: dos círculos se
tocan si la distancia entre sus centros es menor que la suma de sus radios.

Las funciones solo necesitan objetos con atributos x, y (y radius cuando
corresponde), así se pueden probar sin abrir el juego.
"""

import math


def point_distance(x1, y1, x2, y2):
    """Distancia entre dos puntos (teorema de Pitágoras)."""
    return math.hypot(x2 - x1, y2 - y1)


def distance(a, b):
    """Distancia entre los centros de dos objetos con x e y."""
    return point_distance(a.x, a.y, b.x, b.y)


def is_within(a, b, reach):
    """True si b está a menos de 'reach' de a."""
    return distance(a, b) < reach


def circles_overlap(a, b):
    """True si los círculos de a y b se tocan (usa su atributo radius)."""
    return is_within(a, b, a.radius + b.radius)
