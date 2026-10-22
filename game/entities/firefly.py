"""
Las luciérnagas: núcleo brillante + halos que laten.

Pueden estar libres, en la cola del jugador, dispersas (después de un
golpe) o volando hacia el nido. La "fugaz" huye del jugador y vale más.
"""

import math
import random

from kivy.graphics import Color, Ellipse, InstructionGroup
from kivy.metrics import dp

from ..config import (CREAM, DELIVERY_FOLLOW, DELIVERY_REACH,
                      DELIVERY_SHRINK_DISTANCE, FIREFLY_CENTER_COLOR,
                      FIREFLY_FADE_IN_SPEED, FIREFLY_FADE_OUT_TIME,
                      FIREFLY_HALOS, FIREFLY_RADIUS, FIREFLY_SWAY_FREE,
                      FIREFLY_SWAY_OTHER, FIREFLY_VALUE, FIREFLY_WANDER_SPEED,
                      FIREFLY_WANDER_TURN, FLEETING_FLEE_RANGE,
                      FLEETING_FLEE_SPEED, FLEETING_RADIUS, FLEETING_VALUE,
                      GOLD, HALO_GREEN, MAGNET_RANGE, MAGNET_SPEED,
                      SCATTER_FRICTION, SCATTER_TIME, YELLOW)
from ..drawing import set_circle

# Estados posibles de una luciérnaga
FREE = 'free'              # flota por el mapa esperando ser atrapada
TAIL = 'tail'              # sigue al jugador en fila (lo maneja GameScreen)
SCATTERED = 'scattered'    # sale volando porque un murciélago golpeó al jugador
DELIVERING = 'delivering'  # vuela hacia el nido

# Evento que devuelve update() cuando la luciérnaga entra al nido
ARRIVED = 'arrived'


class Firefly:
    """Una luciérnaga. Si se le da 'lifetime', es decorativa (menús) y se
    apaga sola cuando se le acaba el tiempo."""

    def __init__(self, layer, x, y, fleeting=False, lifetime=None):
        self.layer = layer
        self.x, self.y = x, y
        self.fleeting = fleeting       # la fugaz huye y vale el triple
        self.value = FLEETING_VALUE if fleeting else FIREFLY_VALUE
        self.color = GOLD if fleeting else YELLOW
        self.radius = dp(FLEETING_RADIUS if fleeting else FIREFLY_RADIUS)
        self.state = FREE
        self.state_time = 0.0          # segundos en el estado actual
        self.t = random.uniform(0, 100)
        self.phase = random.uniform(0, math.tau)
        self.angle = random.uniform(0, math.tau)  # dirección al pasear
        self.vx = self.vy = 0.0
        self.appear = 0.0              # 0 -> 1 al encenderse
        self.lifetime = lifetime       # solo las decorativas tienen vida
        self.age = 0.0
        self.delay = 0.0               # espera antes de volar al nido
        self.scale = 1.0
        self.finished = False

        halo_color = CREAM if fleeting else HALO_GREEN
        self.group = InstructionGroup()
        self.halos = []
        for factor, alpha in FIREFLY_HALOS:
            color, ellipse = Color(*halo_color, 0), Ellipse()
            self.group.add(color)
            self.group.add(ellipse)
            self.halos.append((color, ellipse, factor, alpha))
        self.core_color = Color(*self.color, 0)
        self.core = Ellipse()
        self.center_color = Color(*FIREFLY_CENTER_COLOR, 0)
        self.center = Ellipse()
        for instruction in (self.core_color, self.core,
                            self.center_color, self.center):
            self.group.add(instruction)
        layer.add(self.group)
        self.draw()

    def set_state(self, state):
        self.state = state
        self.state_time = 0.0

    def update(self, dt, area, player=None, magnet=False, nest=None):
        """Mueve la luciérnaga según su estado. Devuelve ARRIVED cuando
        termina de entrar al nido."""
        self.t += dt
        self.age += dt
        self.state_time += dt
        self.appear = min(1.0, self.appear + dt * FIREFLY_FADE_IN_SPEED)
        event = None

        if self.state == FREE:
            # Pasea: la dirección cambia un poquito al azar.
            self.angle += random.uniform(-1, 1) * FIREFLY_WANDER_TURN * dt
            mx = math.cos(self.angle) * dp(FIREFLY_WANDER_SPEED)
            my = math.sin(self.angle) * dp(FIREFLY_WANDER_SPEED)
            if player is not None:
                dx, dy = player.x - self.x, player.y - self.y
                dist = max(1.0, math.hypot(dx, dy))
                if magnet and dist < dp(MAGNET_RANGE):
                    # Imán: vuela sola hacia el jugador.
                    mx, my = dx / dist * dp(MAGNET_SPEED), dy / dist * dp(MAGNET_SPEED)
                elif self.fleeting and dist < dp(FLEETING_FLEE_RANGE):
                    # La fugaz huye en dirección contraria al jugador.
                    mx = -dx / dist * dp(FLEETING_FLEE_SPEED)
                    my = -dy / dist * dp(FLEETING_FLEE_SPEED)
            self.x += mx * dt
            self.y += my * dt
            if self.lifetime is not None and self.age > self.lifetime + FIREFLY_FADE_OUT_TIME:
                self.finished = True

        elif self.state == SCATTERED:
            self.x += self.vx * dt
            self.y += self.vy * dt
            brake = max(0.0, 1 - SCATTER_FRICTION * dt)
            self.vx *= brake
            self.vy *= brake
            if self.state_time > SCATTER_TIME:
                self.set_state(FREE)

        elif self.state == DELIVERING:
            if self.delay > 0:
                self.delay -= dt  # salen una detrás de otra
            else:
                dx, dy = nest.x - self.x, nest.y - self.y
                dist = math.hypot(dx, dy)
                k = min(1.0, dt * DELIVERY_FOLLOW)  # interpolación: se acerca de a poco
                self.x += dx * k
                self.y += dy * k
                self.scale = max(0.3, min(1.0, dist / dp(DELIVERY_SHRINK_DISTANCE)))
                if dist < dp(DELIVERY_REACH):
                    self.finished = True
                    event = ARRIVED

        # Rebote en los bordes del área (solo cuando vuela suelta).
        if self.state in (FREE, SCATTERED):
            xmin, ymin, xmax, ymax = area
            if not xmin <= self.x <= xmax:
                self.x = min(max(self.x, xmin), xmax)
                self.angle = math.pi - self.angle
                self.vx = -self.vx
            if not ymin <= self.y <= ymax:
                self.y = min(max(self.y, ymin), ymax)
                self.angle = -self.angle
                self.vy = -self.vy

        self.draw()
        return event

    def draw(self):
        alpha = self.appear
        if self.lifetime is not None and self.age > self.lifetime:
            # Se apaga lento al final de su vida.
            alpha *= max(0.0, 1 - (self.age - self.lifetime) / FIREFLY_FADE_OUT_TIME)
        pulse = 1 + 0.18 * math.sin(self.t * 4 + self.phase)   # el halo late
        glow = 0.85 + 0.15 * math.sin(self.t * 9 + self.phase * 2)
        if self.fleeting:
            glow *= 0.8 + 0.2 * math.sin(self.t * 20)  # titila nerviosa

        # Vaivén suave con seno y coseno (más amplio cuando está libre).
        amplitude = dp(FIREFLY_SWAY_FREE if self.state == FREE else FIREFLY_SWAY_OTHER)
        self.cx = self.x + math.sin(self.t * 1.3 + self.phase) * amplitude
        self.cy = self.y + math.cos(self.t * 1.0 + self.phase * 1.3) * amplitude * 0.6

        r = self.radius * self.scale
        for color, ellipse, factor, halo_alpha in self.halos:
            color.a = halo_alpha * alpha * glow
            set_circle(ellipse, self.cx, self.cy, r * factor * pulse)
        self.core_color.a = alpha
        set_circle(self.core, self.cx, self.cy, r)
        self.center_color.a = alpha * 0.9
        set_circle(self.center, self.cx, self.cy, r * 0.45)

    def remove(self):
        self.layer.remove(self.group)
