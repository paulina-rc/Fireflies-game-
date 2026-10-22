"""
El murciélago: el enemigo del juego.

Es una silueta con alas que aletean (mallas de triángulos) y ojos rojos.
Persigue al jugador girando poco a poco, así se le puede esquivar.
"""

import math
import random

from kivy.graphics import Color, Ellipse, InstructionGroup, Mesh, Triangle
from kivy.metrics import dp

from ..config import (BAT_AURA_COLOR, BAT_COLOR, BAT_MAX_TURN, BAT_RADIUS,
                      BAT_SIZE, BAT_SPEED_WOBBLE, BAT_STUN_SPEED_BOOST,
                      EYE_RED, FROZEN_BAT_BODY, ICE_BLUE)
from ..drawing import set_circle


class Bat:
    """Un murciélago que persigue un objetivo (el jugador)."""

    # Contorno de un ala (lado derecho), en unidades del tamaño del murciélago.
    # Cada punto es (x, y, cuánto se mueve con el aleteo). Es la forma del
    # dibujo, no un valor de juego.
    WING = [(0.25, 0.22, 0.00), (0.95, 0.42, 0.45), (1.70, 0.30, 0.70),
            (1.40, -0.10, 0.50), (1.10, 0.02, 0.35), (0.80, -0.22, 0.25),
            (0.50, -0.05, 0.12), (0.25, -0.22, 0.00)]

    def __init__(self, layer, x, y, speed):
        self.layer = layer
        self.x, self.y = x, y
        self.speed = speed
        self.size = dp(BAT_SIZE)
        self.radius = dp(BAT_RADIUS)   # radio de colisión
        self.angle = random.uniform(0, math.tau)
        self.t = random.uniform(0, 10)
        self.stunned = 0.0   # después de golpear, se aleja un momento
        self.frozen = False

        self.group = InstructionGroup()
        self.aura_color = Color(*BAT_AURA_COLOR)
        self.aura = Ellipse()
        self.body_color = Color(*BAT_COLOR, 1)
        self.left_wing = Mesh(mode='triangle_fan')
        self.right_wing = Mesh(mode='triangle_fan')
        indices = list(range(len(self.WING) + 1))
        self.left_wing.indices = indices
        self.right_wing.indices = indices
        self.body = Ellipse()
        self.head = Ellipse()
        self.left_ear = Triangle()
        self.right_ear = Triangle()
        self.eye_glow_color = Color(*EYE_RED, 0.35)
        self.eye_glows = [Ellipse(), Ellipse()]
        self.eye_color = Color(*EYE_RED, 1)
        self.eyes = [Ellipse(), Ellipse()]
        for instruction in (self.aura_color, self.aura, self.body_color,
                            self.left_wing, self.right_wing, self.body,
                            self.head, self.left_ear, self.right_ear,
                            self.eye_glow_color, *self.eye_glows,
                            self.eye_color, *self.eyes):
            self.group.add(instruction)
        layer.add(self.group)
        self.draw()

    def update(self, dt, target_x, target_y, area):
        if not self.frozen:
            self.t += dt
            if self.stunned > 0:
                self.stunned -= dt
            else:
                # Giro suave: calcula hacia dónde debería mirar y gira
                # como máximo BAT_MAX_TURN radianes por segundo.
                wanted = math.atan2(target_y - self.y, target_x - self.x)
                difference = (wanted - self.angle + math.pi) % math.tau - math.pi
                turn = BAT_MAX_TURN * dt
                self.angle += max(-turn, min(turn, difference))
            speed = self.speed * (1 + BAT_SPEED_WOBBLE * math.sin(self.t * 1.7))
            if self.stunned > 0:
                speed *= BAT_STUN_SPEED_BOOST
            self.x += math.cos(self.angle) * speed * dt
            self.y += math.sin(self.angle) * speed * dt
            xmin, ymin, xmax, ymax = area
            if not xmin <= self.x <= xmax:
                self.x = min(max(self.x, xmin), xmax)
                self.angle = math.pi - self.angle
            if not ymin <= self.y <= ymax:
                self.y = min(max(self.y, ymin), ymax)
                self.angle = -self.angle
        self.draw()

    def draw(self):
        s = self.size
        x0 = self.x
        if self.frozen:
            y0, flap = self.y, 0.2  # quieto, con las alas a medio abrir
            self.body_color.rgba = FROZEN_BAT_BODY
            self.aura_color.rgba = (*ICE_BLUE, 0.22)
            self.eye_color.rgba = (*ICE_BLUE, 1)
            self.eye_glow_color.rgba = (*ICE_BLUE, 0.3)
        else:
            y0 = self.y + math.sin(self.t * 6) * dp(3)  # sube y baja al volar
            flap = math.sin(self.t * 14)
            self.body_color.rgba = (*BAT_COLOR, 1)
            self.aura_color.rgba = BAT_AURA_COLOR
            self.eye_color.rgba = (*EYE_RED, 1)
            self.eye_glow_color.rgba = (*EYE_RED, 0.35)

        set_circle(self.aura, x0, y0, s * 1.7)

        # Alas: abanico de triángulos desde el hombro hacia el contorno.
        for side, mesh in ((1, self.right_wing), (-1, self.left_wing)):
            vertices = [x0 + side * 0.2 * s, y0, 0, 0]
            for px, py, move in self.WING:
                vertices += [x0 + side * px * s, y0 + (py + move * flap) * s, 0, 0]
            mesh.vertices = vertices

        self.body.pos = (x0 - 0.31 * s, y0 - 0.52 * s)
        self.body.size = (0.62 * s, 0.95 * s)
        self.head.pos = (x0 - 0.27 * s, y0 + 0.17 * s)
        self.head.size = (0.55 * s, 0.5 * s)
        self.left_ear.points = [x0 - 0.26 * s, y0 + 0.55 * s,
                                x0 - 0.06 * s, y0 + 0.6 * s,
                                x0 - 0.22 * s, y0 + 0.92 * s]
        self.right_ear.points = [x0 + 0.26 * s, y0 + 0.55 * s,
                                 x0 + 0.06 * s, y0 + 0.6 * s,
                                 x0 + 0.22 * s, y0 + 0.92 * s]
        # Los ojos se corren un poquito hacia donde vuela.
        look = math.cos(self.angle) * 0.05 * s
        for side, eye, glow in ((-1, self.eyes[0], self.eye_glows[0]),
                                (1, self.eyes[1], self.eye_glows[1])):
            ex, ey = x0 + side * 0.12 * s + look, y0 + 0.44 * s
            set_circle(glow, ex, ey, 0.18 * s)
            set_circle(eye, ex, ey, 0.07 * s)

    def remove(self):
        self.layer.remove(self.group)
