"""
Power-ups: objetos especiales que aparecen un rato en el mapa.

  luna azul (moon)       -> congela a los murciélagos
  estrella dorada (star) -> imán de luciérnagas
  corazón (heart)        -> +1 vida
"""

import math

from kivy.graphics import Color, Ellipse, InstructionGroup, Mesh, Triangle
from kivy.metrics import dp

from ..config import (POWERUP_COLORS, POWERUP_HALOS, POWERUP_LIFETIME,
                      POWERUP_MOON, POWERUP_RADIUS, POWERUP_STAR,
                      POWERUP_WARNING_TIME)
from ..drawing import place_heart, set_circle

MOON_STEPS = 12   # tramos de la media luna
STAR_POINTS = 5   # puntas de la estrella


class PowerUp:
    """Un power-up flotando. 'kind' es POWERUP_MOON, POWERUP_STAR o
    POWERUP_HEART."""

    def __init__(self, layer, kind, x, y):
        self.layer = layer
        self.kind = kind
        self.x, self.y = x, y
        self.radius = dp(POWERUP_RADIUS)
        self.age = 0.0
        self.t = 0.0
        self.finished = False
        color = POWERUP_COLORS[kind]

        self.group = InstructionGroup()
        self.halos = []
        for factor, alpha in POWERUP_HALOS:
            c, e = Color(*color, alpha), Ellipse()
            self.group.add(c)
            self.group.add(e)
            self.halos.append((c, e, factor, alpha))
        self.shape_color = Color(*color, 1)
        self.group.add(self.shape_color)
        if kind == POWERUP_MOON:
            self.mesh = Mesh(mode='triangle_strip', indices=list(range(2 * (MOON_STEPS + 1))))
            self.group.add(self.mesh)
        elif kind == POWERUP_STAR:
            self.mesh = Mesh(mode='triangle_fan', indices=list(range(2 * STAR_POINTS + 2)))
            self.group.add(self.mesh)
        else:
            self.circle_1, self.circle_2 = Ellipse(), Ellipse()
            self.triangle = Triangle()
            for instruction in (self.circle_1, self.circle_2, self.triangle):
                self.group.add(instruction)
        layer.add(self.group)
        self.draw()

    def update(self, dt):
        self.age += dt
        self.t += dt
        if self.age >= POWERUP_LIFETIME:
            self.finished = True
        self.draw()

    def draw(self):
        alpha = min(1.0, self.age / 0.3)
        if POWERUP_LIFETIME - self.age < POWERUP_WARNING_TIME:
            alpha *= 0.35 + 0.65 * (0.5 + 0.5 * math.cos(self.t * 16))  # aviso
        cx = self.x
        cy = self.y + math.sin(self.t * 2.5) * dp(4)  # flota
        r = self.radius
        pulse = 1 + 0.12 * math.sin(self.t * 4)
        for color, ellipse, factor, halo_alpha in self.halos:
            color.a = halo_alpha * alpha
            set_circle(ellipse, cx, cy, r * factor * pulse)
        self.shape_color.a = alpha

        if self.kind == POWERUP_MOON:
            # Media luna: tira de triángulos entre una media circunferencia
            # (borde de afuera) y una media elipse delgada (borde de adentro).
            vertices = []
            for k in range(MOON_STEPS + 1):
                a = -math.pi / 2 + math.pi * k / MOON_STEPS
                vertices += [cx - 0.25 * r + r * math.cos(a), cy + r * math.sin(a), 0, 0,
                             cx - 0.25 * r + 0.35 * r * math.cos(a), cy + r * math.sin(a), 0, 0]
            self.mesh.vertices = vertices
        elif self.kind == POWERUP_STAR:
            # Estrella: abanico desde el centro con radios alternados
            # (punta larga, hueco corto). Gira despacio.
            vertices = [cx, cy, 0, 0]
            for k in range(2 * STAR_POINTS + 1):
                a = math.pi / 2 + k * math.pi / STAR_POINTS + self.t * 0.6
                length = r * 1.15 if k % 2 == 0 else r * 0.5
                vertices += [cx + math.cos(a) * length, cy + math.sin(a) * length, 0, 0]
            self.mesh.vertices = vertices
        else:
            place_heart(self.circle_1, self.circle_2, self.triangle, cx, cy, r * 0.95)

    def remove(self):
        self.layer.remove(self.group)
