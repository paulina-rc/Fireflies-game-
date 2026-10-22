"""
Reglas de las noches (niveles) y de la dificultad.

LevelManager guarda en qué noche vamos y calcula la meta, la cantidad y
velocidad de murciélagos y cuántas luciérnagas puede haber sueltas.
No usa Kivy, así se puede probar con unittest.
"""

from ..config import (BAT_BASE_SPEED, BAT_MAX_SPEED_FACTOR, BAT_SPEED_INCREASE,
                      DELIVERY_MULTIPLIERS, EXTRA_BATS, FIRST_NIGHT_GOAL,
                      FLEETING_MIN_NIGHT, FREE_FIREFLIES_BASE,
                      FREE_FIREFLIES_MAX, GOAL_INCREASE_PER_NIGHT)


def delivery_multiplier(count):
    """Multiplicador de una entrega según cuántas luciérnagas se llevan
    (con la configuración actual: 5 o más x2, 10 o más x3)."""
    for minimum, multiplier in DELIVERY_MULTIPLIERS:
        if count >= minimum:
            return multiplier
    return 1


class LevelManager:
    """Guarda en qué noche vamos y calcula las reglas de cada noche."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Vuelve a la Noche 1 (partida nueva)."""
        self.night = 1
        self.delivered_tonight = 0  # luciérnagas entregadas en esta noche
        self.delivered_total = 0    # en toda la partida

    @staticmethod
    def goal_for(night):
        """Meta de una noche: 10 en la Noche 1, y +5 por cada noche."""
        return FIRST_NIGHT_GOAL + GOAL_INCREASE_PER_NIGHT * (night - 1)

    @property
    def goal(self):
        return self.goal_for(self.night)

    @property
    def bat_count(self):
        """Noche 1: 2 murciélagos, y uno más cada noche."""
        return self.night + EXTRA_BATS

    @property
    def bat_speed(self):
        """Velocidad de los murciélagos en dp por segundo. Cada noche son un
        9 % más rápidos, con un tope para que sea justo."""
        factor = min(BAT_MAX_SPEED_FACTOR, 1 + BAT_SPEED_INCREASE * (self.night - 1))
        return BAT_BASE_SPEED * factor

    @property
    def allows_fleeting(self):
        """La luciérnaga fugaz aparece desde la Noche 4."""
        return self.night >= FLEETING_MIN_NIGHT

    @property
    def max_free_fireflies(self):
        return min(FREE_FIREFLIES_MAX, FREE_FIREFLIES_BASE + self.night)

    def register_delivery(self, count):
        """Suma luciérnagas entregadas. Devuelve True si se cumplió la meta."""
        self.delivered_tonight += count
        self.delivered_total += count
        return self.delivered_tonight >= self.goal

    def next_night(self):
        self.night += 1
        self.delivered_tonight = 0
