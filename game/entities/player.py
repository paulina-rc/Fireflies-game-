"""
El jugador: un espíritu de luz.

Se mueve con aceleración y fricción (no se detiene de golpe), deja una
estela y puede hacer un impulso rápido (dash).
"""

import math
from collections import deque

from kivy.graphics import Color, Ellipse, InstructionGroup
from kivy.metrics import dp

from ..config import (DASH_COOLDOWN, DASH_DURATION, DASH_SPEED, GOLD,
                      PLAYER_ACCELERATION, PLAYER_BLINK_ALPHA,
                      PLAYER_BLINK_RATE, PLAYER_DASH_GLOW, PLAYER_FRICTION,
                      PLAYER_HALOS, PLAYER_LIGHT, PLAYER_MAGNET_TINT,
                      PLAYER_RADIUS, TRAIL_FULL_SPEED, TRAIL_INTERVAL,
                      TRAIL_LENGTH)
from ..drawing import mix, set_circle


class Player:
    """El espíritu de luz.

    Como todas las entidades, NO es un widget: agrupa sus dibujos en un
    InstructionGroup y lo agrega a una "capa" (layer). Es más liviano que
    crear un widget por cada objeto.
    """

    def __init__(self, layer, x, y):
        self.layer = layer
        self.x, self.y = x, y
        self.vx = self.vy = 0.0
        self.dir_x, self.dir_y = 1.0, 0.0  # última dirección de movimiento
        self.radius = dp(PLAYER_RADIUS)
        self.t = 0.0
        self.dash_time = 0.0
        self.cooldown = 0.0
        self.invulnerable = 0.0
        self.magnet = False      # lo activa el juego (halo dorado)
        self.visible = True
        self.trail = deque(maxlen=TRAIL_LENGTH)  # últimas posiciones
        self.trail_clock = 0.0

        self.group = InstructionGroup()
        self.trail_dots = []
        for _ in range(TRAIL_LENGTH):
            color, ellipse = Color(*PLAYER_LIGHT, 0), Ellipse()
            self.group.add(color)
            self.group.add(ellipse)
            self.trail_dots.append((color, ellipse))
        self.halos = []
        for factor, alpha in PLAYER_HALOS:
            color, ellipse = Color(*PLAYER_LIGHT, alpha), Ellipse()
            self.group.add(color)
            self.group.add(ellipse)
            self.halos.append((color, ellipse, factor, alpha))
        self.core_color = Color(*PLAYER_LIGHT, 1)
        self.core = Ellipse()
        self.center_color = Color(1, 1, 1, 1)
        self.center = Ellipse()
        for instruction in (self.core_color, self.core,
                            self.center_color, self.center):
            self.group.add(instruction)
        layer.add(self.group)
        self.draw()

    @property
    def is_dashing(self):
        return self.dash_time > 0

    @property
    def dash_progress(self):
        """0 = recién usado, 1 = listo para usar otra vez."""
        return 1 - self.cooldown / DASH_COOLDOWN

    def update(self, dt, dx, dy, area):
        """dx, dy = dirección pedida con el teclado (-1, 0 o 1)."""
        self.t += dt
        length = math.hypot(dx, dy)
        if length:
            dx, dy = dx / length, dy / length  # en diagonal no va más rápido
            self.dir_x, self.dir_y = dx, dy

        if self.dash_time > 0:
            self.dash_time -= dt  # durante el dash no hay control ni fricción
        else:
            # Aceleración: la velocidad cambia de a poco, no de golpe.
            self.vx += dx * dp(PLAYER_ACCELERATION) * dt
            self.vy += dy * dp(PLAYER_ACCELERATION) * dt
            # Fricción: en cada cuadro se pierde una parte de la velocidad.
            brake = max(0.0, 1 - PLAYER_FRICTION * dt)
            self.vx *= brake
            self.vy *= brake

        self.x += self.vx * dt
        self.y += self.vy * dt

        # No puede salir del área de juego.
        xmin, ymin, xmax, ymax = area
        if not xmin <= self.x <= xmax:
            self.x = min(max(self.x, xmin), xmax)
            self.vx = 0
        if not ymin <= self.y <= ymax:
            self.y = min(max(self.y, ymin), ymax)
            self.vy = 0

        self.cooldown = max(0.0, self.cooldown - dt)
        self.invulnerable = max(0.0, self.invulnerable - dt)

        # Guarda una posición para la estela cada TRAIL_INTERVAL segundos.
        self.trail_clock += dt
        if self.trail_clock >= TRAIL_INTERVAL:
            self.trail_clock = 0
            self.trail.append((self.x, self.y))

    def try_dash(self):
        """Hace el impulso si no está en enfriamiento. Devuelve True si salió."""
        if self.cooldown > 0:
            return False
        self.vx = self.dir_x * dp(DASH_SPEED)
        self.vy = self.dir_y * dp(DASH_SPEED)
        self.dash_time = DASH_DURATION
        self.cooldown = DASH_COOLDOWN
        return True

    def draw(self):
        alpha = 1.0
        if not self.visible:
            alpha = 0.0
        elif self.invulnerable > 0 and int(self.t * PLAYER_BLINK_RATE) % 2:
            alpha = PLAYER_BLINK_ALPHA  # parpadeo mientras es invulnerable

        # Estela: círculos más chicos y transparentes mientras más viejos.
        speed = min(1.0, math.hypot(self.vx, self.vy) / max(1.0, dp(TRAIL_FULL_SPEED)))
        positions = list(self.trail)
        for i, (color, ellipse) in enumerate(self.trail_dots):
            if i < len(positions):
                fraction = (i + 1) / len(positions)
                px, py = positions[i]
                color.a = 0.22 * fraction * speed * alpha
                set_circle(ellipse, px, py, self.radius * (0.3 + 0.6 * fraction))
            else:
                color.a = 0

        tone = mix(PLAYER_LIGHT, GOLD, PLAYER_MAGNET_TINT) if self.magnet else PLAYER_LIGHT
        pulse = 1 + 0.08 * math.sin(self.t * 3)
        if self.is_dashing:
            pulse *= PLAYER_DASH_GLOW
        for color, ellipse, factor, halo_alpha in self.halos:
            color.rgba = (*tone, halo_alpha * alpha)
            set_circle(ellipse, self.x, self.y, self.radius * factor * pulse)
        self.core_color.a = alpha
        set_circle(self.core, self.x, self.y, self.radius * 0.8)
        self.center_color.a = alpha
        set_circle(self.center, self.x, self.y, self.radius * 0.45)

    def remove(self):
        self.layer.remove(self.group)
