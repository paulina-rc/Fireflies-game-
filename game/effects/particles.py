"""
Efectos visuales cortos: chispas, texto flotante de puntos y anillos.

Cada efecto tiene update(dt), que devuelve False cuando terminó, y
remove(), que borra sus dibujos de la capa.
"""

import math
import random

from kivy.core.text import Label as CoreLabel
from kivy.graphics import Color, Ellipse, InstructionGroup, Line, Rectangle
from kivy.metrics import dp, sp

from ..config import (FLASH_RING_DURATION, FLASH_RING_RADIUS,
                      FLOATING_TEXT_DURATION, FLOATING_TEXT_RISE,
                      FLOATING_TEXT_SIZE, PARTICLE_FRICTION, PARTICLE_LIFE,
                      PARTICLE_RISE, PARTICLE_SIZE, PARTICLE_SPEED)
from ..drawing import set_circle


class Particle:
    """Chispita que sale disparada, se frena, se encoge y se desvanece."""

    def __init__(self, layer, x, y, color, speed=PARTICLE_SPEED, life=PARTICLE_LIFE):
        self.layer = layer
        angle = random.uniform(0, math.tau)
        velocity = dp(random.uniform(*speed))
        self.vx = math.cos(angle) * velocity
        self.vy = math.sin(angle) * velocity
        self.x, self.y = x, y
        self.life = random.uniform(*life)
        self.age = 0.0
        self.radius = random.uniform(dp(PARTICLE_SIZE[0]), dp(PARTICLE_SIZE[1]))
        self.group = InstructionGroup()
        self.glow_color = Color(*color, 0.15)
        self.glow = Ellipse()
        self.dot_color = Color(*color, 1)
        self.dot = Ellipse()
        for instruction in (self.glow_color, self.glow, self.dot_color, self.dot):
            self.group.add(instruction)
        layer.add(self.group)
        self.update(0)

    def update(self, dt):
        self.age += dt
        if self.age >= self.life:
            return False
        brake = max(0.0, 1 - PARTICLE_FRICTION * dt)  # rozamiento
        self.vx *= brake
        self.vy *= brake
        self.vy += dp(PARTICLE_RISE) * dt   # sube un poquito, como flotando
        self.x += self.vx * dt
        self.y += self.vy * dt
        progress = self.age / self.life
        r = self.radius * (1 - 0.5 * progress)
        self.dot_color.a = 1 - progress
        self.glow_color.a = 0.15 * (1 - progress)
        set_circle(self.dot, self.x, self.y, r)
        set_circle(self.glow, self.x, self.y, r * 2.2)
        return True

    def remove(self):
        self.layer.remove(self.group)


class FloatingText:
    """Texto como "+12" que sube y desaparece. CoreLabel convierte el texto
    en una textura que se dibuja con un Rectangle."""

    def __init__(self, layer, x, y, text, color, size=None, duration=FLOATING_TEXT_DURATION):
        self.layer = layer
        label = CoreLabel(text=text, font_size=size or sp(FLOATING_TEXT_SIZE), bold=True)
        label.refresh()
        texture = label.texture
        self.x = x - texture.width / 2
        self.y = y
        self.duration = duration
        self.age = 0.0
        self.group = InstructionGroup()
        self.color = Color(*color, 1)  # tiñe la textura blanca del texto
        self.rect = Rectangle(texture=texture, size=texture.size, pos=(self.x, self.y))
        self.group.add(self.color)
        self.group.add(self.rect)
        layer.add(self.group)

    def update(self, dt):
        self.age += dt
        progress = self.age / self.duration
        self.rect.pos = (self.x, self.y + dp(FLOATING_TEXT_RISE) * progress)
        self.color.a = max(0.0, 1 - progress ** 2)
        return progress < 1

    def remove(self):
        self.layer.remove(self.group)


class FlashRing:
    """Anillo que se agranda y se desvanece (al entregar o recoger algo)."""

    def __init__(self, layer, x, y, color, final_radius=None, duration=FLASH_RING_DURATION):
        self.layer = layer
        self.x, self.y = x, y
        self.final_radius = final_radius or dp(FLASH_RING_RADIUS)
        self.duration = duration
        self.age = 0.0
        self.group = InstructionGroup()
        self.color = Color(*color, 0.8)
        self.line = Line(circle=(x, y, 1), width=dp(2))
        self.group.add(self.color)
        self.group.add(self.line)
        layer.add(self.group)

    def update(self, dt):
        self.age += dt
        progress = min(1.0, self.age / self.duration)
        smooth = 1 - (1 - progress) ** 2  # rápido al inicio, lento al final
        self.color.a = 0.8 * (1 - progress)
        self.line.circle = (self.x, self.y, max(1.0, self.final_radius * smooth))
        return progress < 1

    def remove(self):
        self.layer.remove(self.group)
