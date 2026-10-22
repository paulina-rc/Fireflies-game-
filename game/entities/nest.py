"""
El nido: círculo brillante donde se entregan las luciérnagas.

Su posición se guarda en valores relativos (rx, ry de 0 a 1) para que se
adapte al tamaño de la ventana.
"""

import math
import random

from kivy.graphics import Color, Ellipse, InstructionGroup, Line
from kivy.metrics import dp

from ..config import (CREAM, NEST_AREA_X, NEST_AREA_Y, NEST_FLASH_DECAY,
                      NEST_HALOS, NEST_MIN_DISTANCE_FROM_PLAYER,
                      NEST_ORBIT_DOTS, NEST_ORBIT_SPEED, NEST_PLACEMENT_TRIES,
                      NEST_RADIUS, YELLOW)
from ..drawing import set_circle
from ..systems.collisions import point_distance


class Nest:
    """El nido, con halos, anillos y puntitos que giran alrededor."""

    def __init__(self, layer):
        self.layer = layer
        self.radius = dp(NEST_RADIUS)
        self.rx, self.ry = 0.5, 0.5
        self.x = self.y = 0.0
        self.t = 0.0
        self.flash = 0.0  # 1 al entregar, baja hasta 0

        self.group = InstructionGroup()
        self.halos = []
        for factor, alpha in NEST_HALOS:
            color, ellipse = Color(*YELLOW, alpha), Ellipse()
            self.group.add(color)
            self.group.add(ellipse)
            self.halos.append((ellipse, factor))
        self.flash_color = Color(*CREAM, 0)
        self.flash_disc = Ellipse()
        self.ring_color = Color(*YELLOW, 0.7)
        self.ring = Line(width=dp(2))
        self.inner_ring_color = Color(*YELLOW, 0.25)
        self.inner_ring = Line(width=dp(1.2))
        for instruction in (self.flash_color, self.flash_disc,
                            self.ring_color, self.ring,
                            self.inner_ring_color, self.inner_ring):
            self.group.add(instruction)
        # Puntitos que giran alrededor del nido
        self.orbit_color = Color(*CREAM, 0.8)
        self.group.add(self.orbit_color)
        self.orbit = [Ellipse() for _ in range(NEST_ORBIT_DOTS)]
        for dot in self.orbit:
            self.group.add(dot)
        layer.add(self.group)

    def move(self, area, avoid=None):
        """Elige un lugar nuevo, lejos de 'avoid' (la posición del jugador)."""
        xmin, ymin, xmax, ymax = area
        for _ in range(NEST_PLACEMENT_TRIES):
            rx, ry = random.uniform(*NEST_AREA_X), random.uniform(*NEST_AREA_Y)
            x = xmin + rx * (xmax - xmin)
            y = ymin + ry * (ymax - ymin)
            if avoid is None or point_distance(x, y, *avoid) > dp(NEST_MIN_DISTANCE_FROM_PLAYER):
                break
        self.rx, self.ry = rx, ry

    def update(self, dt, area):
        self.t += dt
        self.flash = max(0.0, self.flash - dt * NEST_FLASH_DECAY)
        xmin, ymin, xmax, ymax = area
        self.x = xmin + self.rx * (xmax - xmin)
        self.y = ymin + self.ry * (ymax - ymin)
        self.draw()

    def draw(self):
        pulse = 0.85 + 0.15 * math.sin(self.t * 2.5)
        r = self.radius * (1 + 0.15 * self.flash)
        for ellipse, factor in self.halos:
            set_circle(ellipse, self.x, self.y, r * factor * pulse)
        # Destello: un disco claro que crece y se apaga al entregar.
        self.flash_color.a = 0.45 * self.flash
        set_circle(self.flash_disc, self.x, self.y, r * (1.0 + (1 - self.flash) * 0.8))
        self.ring_color.a = 0.55 + 0.3 * pulse + 0.3 * self.flash
        self.ring.circle = (self.x, self.y, r)
        self.inner_ring.circle = (self.x, self.y, r * 0.68)
        for k, dot in enumerate(self.orbit):
            angle = self.t * NEST_ORBIT_SPEED + k * math.tau / len(self.orbit)
            set_circle(dot, self.x + math.cos(angle) * r * 1.12,
                       self.y + math.sin(angle) * r * 1.12, dp(2.2))

    def remove(self):
        self.layer.remove(self.group)
