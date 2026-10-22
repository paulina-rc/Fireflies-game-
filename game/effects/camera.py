"""
Sacudida de pantalla (screen shake).

Se agrega un Translate al canvas de un widget (el "mundo": fondo + juego).
Al golpear al jugador el Translate se mueve unos píxeles al azar y la
fuerza va bajando. El HUD está fuera de ese widget, así que no se mueve.
"""

import random

from kivy.graphics import PopMatrix, PushMatrix, Translate
from kivy.metrics import dp

from ..config import SHAKE_DECAY, SHAKE_STRENGTH


class ScreenShake:
    """Sacude un widget y todo lo que tiene adentro."""

    def __init__(self, widget):
        # PushMatrix/PopMatrix guardan y restauran la posición original,
        # así el Translate solo afecta a este widget y a sus hijos.
        with widget.canvas.before:
            PushMatrix()
            self.translate = Translate(0, 0)
        with widget.canvas.after:
            PopMatrix()
        self.intensity = 0.0  # 0..1

    def shake(self):
        """Empieza una sacudida con toda la fuerza."""
        self.intensity = 1.0

    def reset(self):
        self.intensity = 0.0
        self.translate.xy = (0, 0)

    def update(self, dt):
        """Mueve el mundo unos píxeles al azar; la fuerza va bajando."""
        self.intensity = max(0.0, self.intensity - dt * SHAKE_DECAY)
        strength = dp(SHAKE_STRENGTH) * self.intensity ** 2
        self.translate.xy = (random.uniform(-strength, strength),
                             random.uniform(-strength, strength))
