"""
Adornos animados de los menús.

DecorativeSwarm: luciérnagas que aparecen y se apagan solas en el fondo.
Showcase: muestra un elemento del juego animado (en "Cómo jugar").
"""

import random

from kivy.graphics import InstructionGroup, PopMatrix, PushMatrix, Scale, Translate
from kivy.metrics import dp
from kivy.uix.widget import Widget

from ..config import (SWARM_FLEETING_CHANCE, SWARM_LIFETIME, SWARM_MAX,
                      SWARM_SPAWN_DELAY)
from ..entities.firefly import Firefly

SWARM_SIDE_MARGIN = 20    # margen para que no salgan de la pantalla
SWARM_BOTTOM = 0.15       # no bajan hasta los juncos


class DecorativeSwarm(Widget):
    """Luciérnagas de adorno para los menús (con vida limitada)."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fireflies = []
        self.wait = 0.0

    def area(self):
        return (self.x + dp(SWARM_SIDE_MARGIN), self.y + self.height * SWARM_BOTTOM,
                self.right - dp(SWARM_SIDE_MARGIN), self.top - dp(SWARM_SIDE_MARGIN))

    def update(self, dt):
        area = self.area()
        self.wait -= dt
        if self.wait <= 0 and len(self.fireflies) < SWARM_MAX:
            xmin, ymin, xmax, ymax = area
            self.fireflies.append(Firefly(
                self.canvas, random.uniform(xmin, xmax), random.uniform(ymin, ymax),
                fleeting=random.random() < SWARM_FLEETING_CHANCE,
                lifetime=random.uniform(*SWARM_LIFETIME)))
            self.wait = random.uniform(*SWARM_SPAWN_DELAY)
        for firefly in self.fireflies[:]:
            firefly.update(dt, area)
            if firefly.finished:
                firefly.remove()
                self.fireflies.remove(firefly)

    def clear(self):
        for firefly in self.fireflies:
            firefly.remove()
        self.fireflies = []


class Showcase(Widget):
    """Dibuja un elemento del juego centrado y animado.

    factory: función que recibe una capa y crea el elemento en (0, 0).
    Translate lo lleva al centro del widget y Scale lo agranda o achica.
    """

    def __init__(self, factory, scale=1.0, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            PushMatrix()
            self.translate = Translate(0, 0)
            Scale(x=scale, y=scale, z=1)
        self.group = InstructionGroup()
        self.canvas.add(self.group)
        with self.canvas.after:
            PopMatrix()
        self.entity = factory(self.group)

    def animate(self, dt):
        # El centro se actualiza en cada cuadro, así siempre sigue al
        # widget aunque la grilla lo reacomode.
        self.translate.xy = self.center
        self.entity.t += dt
        self.entity.x = self.entity.y = 0
        self.entity.draw()
